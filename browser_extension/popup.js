const DEFAULT_BACKEND = "https://ecommerce-ai-copilot-backend.onrender.com";
let lastWorkspaceAnalysis = null;

function $(id) {
  return document.getElementById(id);
}

function setStatus(message, isError = false) {
  const node = $("status");
  node.textContent = message;
  node.style.color = isError ? "#b91c1c" : "#15803d";
}


function escapeHTML(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function listItems(values, emptyMessage = "No signals detected yet.") {
  const items = (values || []).filter(Boolean).slice(0, 6);
  if (!items.length) {
    return `<div class="empty">${escapeHTML(emptyMessage)}</div>`;
  }
  return `<ul>${items.map((value) => `<li>${escapeHTML(value)}</li>`).join("")}</ul>`;
}

function themeItems(themes, emptyMessage = "No repeated theme detected yet.") {
  const items = (themes || []).slice(0, 6);
  if (!items.length) {
    return `<div class="empty">${escapeHTML(emptyMessage)}</div>`;
  }

  return `<ul>${items.map((theme) => {
    const quotes = (theme.evidence_quotes || [])
      .slice(0, 2)
      .map((quote) => `<blockquote>${escapeHTML(quote)}</blockquote>`)
      .join("");
    const count = theme.evidence_count ? ` <span class="pill">${escapeHTML(theme.evidence_count)}</span>` : "";
    return `<li><strong>${escapeHTML(theme.label || "Theme")}</strong>${count}${quotes}</li>`;
  }).join("")}</ul>`;
}

function renderWorkspaceAnalysis(body) {
  const summary = $("analysisSummary");
  if (!summary) return;

  summary.innerHTML = `
    <div class="metric-grid">
      <div class="metric-card">
        <span>Products</span>
        <strong>${escapeHTML(body.product_count ?? 0)}</strong>
      </div>
      <div class="metric-card">
        <span>Total reviews</span>
        <strong>${escapeHTML(body.total_reviews ?? 0)}</strong>
      </div>
      <div class="metric-card">
        <span>High-signal</span>
        <strong>${escapeHTML(body.high_signal_review_count ?? 0)}</strong>
      </div>
    </div>

    <div class="insight-section">
      <h3>Top pain points</h3>
      ${themeItems(body.common_pain_points)}
    </div>

    <div class="insight-section">
      <h3>Buyer objections</h3>
      ${themeItems(body.buyer_objections)}
    </div>

    <div class="insight-section">
      <h3>Creative angles</h3>
      ${listItems(body.creative_angles)}
    </div>

    <div class="insight-section">
      <h3>Hooks</h3>
      ${listItems(body.hooks)}
    </div>
  `;
}



function compactThemeLines(title, themes) {
  const rows = [`${title}:`];
  const items = (themes || []).slice(0, 6);
  if (!items.length) {
    rows.push("- No repeated signals detected yet.");
    return rows;
  }

  for (const theme of items) {
    const count = theme.evidence_count ? ` (${theme.evidence_count})` : "";
    rows.push(`- ${theme.label || "Theme"}${count}`);
    for (const quote of (theme.evidence_quotes || []).slice(0, 2)) {
      rows.push(`  Evidence: ${quote}`);
    }
  }
  return rows;
}

function compactListLines(title, values) {
  const rows = [`${title}:`];
  const items = (values || []).filter(Boolean).slice(0, 8);
  if (!items.length) {
    rows.push("- No items generated yet.");
    return rows;
  }
  for (const item of items) {
    rows.push(`- ${item}`);
  }
  return rows;
}

function compactProductLines(products) {
  const rows = ["Collected products:"];
  const items = products || [];
  if (!items.length) {
    rows.push("- No products collected yet.");
    return rows;
  }

  for (const product of items) {
    const platform = String(product.platform || "web").toLowerCase();
    const reviewCount = (product.reviews || []).length;
    rows.push(`- ${platform} - ${shortProductTitle(product)} - ${reviewCount} review(s)`);
  }
  return rows;
}

function buildWorkspacePayload(products) {
  return {
    workspace_id: `extension_workspace_${Date.now()}`,
    source: "chrome_extension",
    output_language: "en",
    products: products || []
  };
}

async function copyTextToClipboard(text) {
  await navigator.clipboard.writeText(text);
}


async function waitForTabLoad(tabId) {
  return new Promise((resolve) => {
    const timeout = setTimeout(() => {
      chrome.tabs.onUpdated.removeListener(listener);
      resolve();
    }, 5000);

    function listener(updatedTabId, changeInfo) {
      if (updatedTabId === tabId && changeInfo.status === "complete") {
        clearTimeout(timeout);
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    }

    chrome.tabs.onUpdated.addListener(listener);
  });
}

async function openInWebWorkspace() {
  const backendUrl = $("backendUrl").value.trim().replace(/\/$/, "") || DEFAULT_BACKEND;
  await chrome.storage.local.set({ backendUrl });

  const { products } = await getSavedProducts();
  if (!products.length) {
    throw new Error("Save or collect products before opening the web workspace.");
  }

  const payload = buildWorkspacePayload(products);
  const payloadJson = JSON.stringify(payload);
  const targetUrl = `${backendUrl}/?extension_workspace=1`;

  const tab = await chrome.tabs.create({ url: targetUrl, active: true });
  if (!tab.id) {
    throw new Error("Could not open web workspace tab.");
  }

  await waitForTabLoad(tab.id);

  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    args: [payloadJson],
    func: (workspacePayload) => {
      localStorage.setItem("crossgrowth_extension_workspace", workspacePayload);
      window.dispatchEvent(new CustomEvent("crossgrowth-extension-workspace-ready"));
    }
  });

  setStatus("Opened workspace in web app.");
}


async function copyInsights() {
  if (!lastWorkspaceAnalysis) {
    throw new Error("Analyze a workspace before copying insights.");
  }

  const { products } = await getSavedProducts();
  const body = lastWorkspaceAnalysis;

  const lines = [
    "CrossGrowth Review Workspace Insights",
    "",
    `Products: ${body.product_count ?? 0}`,
    `Total reviews: ${body.total_reviews ?? 0}`,
    `High-signal reviews: ${body.high_signal_review_count ?? 0}`,
    "",
    ...compactProductLines(products),
    "",
    ...compactThemeLines("Top pain points", body.common_pain_points),
    "",
    ...compactThemeLines("Buyer objections", body.buyer_objections),
    "",
    ...compactListLines("Creative angles", body.creative_angles),
    "",
    ...compactListLines("Hooks", body.hooks)
  ];

  await copyTextToClipboard(lines.join("\n"));
  setStatus("Copied insights to clipboard.");
}

async function copyWorkspaceJson() {
  const { products } = await getSavedProducts();
  if (!products.length) {
    throw new Error("Save or collect products before copying workspace JSON.");
  }

  await copyTextToClipboard(JSON.stringify(buildWorkspacePayload(products), null, 2));
  setStatus("Copied workspace JSON to clipboard.");
}


async function getSavedProducts() {
  const result = await chrome.storage.local.get(["workspaceProducts", "backendUrl"]);
  return {
    products: result.workspaceProducts || [],
    backendUrl: result.backendUrl || DEFAULT_BACKEND
  };
}

async function setSavedProducts(products) {
  await chrome.storage.local.set({ workspaceProducts: products });
  await updateStats();
}


function shortProductTitle(product) {
  const title = String(product?.title || product?.url || "Untitled product").trim();
  return title.length > 86 ? `${title.slice(0, 83)}...` : title;
}


function captureDiagnosticMessage(product) {
  const metadata = product?.metadata || {};
  const status = metadata.review_visibility_status;

  if (metadata.sign_in_required || status === "sign_in_required") {
    return "Amazon sign-in required. The extension only collects visible page content.";
  }

  if (
    status === "no_visible_reviews_on_product_page" ||
    status === "no_visible_reviews_on_reviews_page" ||
    status === "no_visible_reviews"
  ) {
    return "Product info captured. No visible reviews found. Scroll to reviews or open a visible review page.";
  }

  return "";
}

function productSourceLabel(product) {
  const platform = String(product?.platform || "web").toLowerCase();
  const reviewCount = (product?.reviews || []).length;
  const reviewLabel = reviewCount === 1 ? "review" : "reviews";
  return `${platform} - ${reviewCount} ${reviewLabel}`;
}

function renderSavedProducts(products) {
  const target = $("collectedProducts");
  if (!target) return;

  const items = products || [];
  if (!items.length) {
    target.innerHTML = "";
    return;
  }

  target.innerHTML = `
    <div class="collected-header">Collected products</div>
    <ol>
      ${items.map((product) => `
        <li>
          <div class="collected-title">${escapeHTML(shortProductTitle(product))}</div>
          <div class="collected-meta">${escapeHTML(productSourceLabel(product))}</div>
        </li>
      `).join("")}
    </ol>
  `;
}


async function updateStats() {
  const { products, backendUrl } = await getSavedProducts();
  $("backendUrl").value = backendUrl;
  $("savedCount").textContent = String(products.length);
  $("reviewCount").textContent = String(products.reduce((sum, product) => sum + (product.reviews || []).length, 0));
  renderSavedProducts(products);
}

async function getActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tabs.length || !tabs[0].id) {
    throw new Error("No active tab found.");
  }
  return tabs[0];
}


function isCollectableTabUrl(url) {
  const value = String(url || "").toLowerCase();
  return (
    value.includes("amazon.") ||
    value.includes("tiktok.") ||
    value.includes("platform=amazon") ||
    value.includes("platform=tiktok")
  );
}

async function extractProductFromTab(tab) {
  if (!tab || !tab.id) {
    throw new Error("No tab id available.");
  }

  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ["content.js"]
  });

  const results = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => window.CrossGrowthReviewCollector.extractCurrentPage()
  });

  const product = results && results[0] ? results[0].result : null;
  if (!product || !product.title) {
    throw new Error("Could not extract product details from this tab.");
  }
  return product;
}

function mergeProductsByUrl(existingProducts, newProducts) {
  const byUrl = new Map();
  for (const product of existingProducts || []) {
    if (product && product.url) {
      byUrl.set(product.url, product);
    }
  }
  for (const product of newProducts || []) {
    if (product && product.url) {
      byUrl.set(product.url, product);
    }
  }
  return Array.from(byUrl.values());
}


async function extractCurrentProduct() {
  const tab = await getActiveTab();
  return extractProductFromTab(tab);
}

async function saveCurrentProduct() {
  setStatus("Collecting current tab...");
  const product = await extractCurrentProduct();
  const { products } = await getSavedProducts();

  const deduped = products.filter((item) => item.url !== product.url);
  deduped.push(product);

  await setSavedProducts(deduped);
  $("previewCard").hidden = false;
  $("preview").textContent = JSON.stringify(product, null, 2);
  const diagnostic = captureDiagnosticMessage(product);
  const diagnosticSuffix = diagnostic ? ` ${diagnostic}` : "";
  setStatus(`Saved: ${product.title || product.url}. Reviews: ${(product.reviews || []).length}.${diagnosticSuffix}`);
}


async function collectOpenTabs() {
  setStatus("Collecting open Amazon/TikTok tabs...");

  const tabs = await chrome.tabs.query({ currentWindow: true });
  const candidates = tabs.filter((tab) => tab.id && isCollectableTabUrl(tab.url));

  if (!candidates.length) {
    throw new Error("No Amazon or TikTok tabs found in this window.");
  }

  const collected = [];
  const failures = [];

  for (const tab of candidates) {
    try {
      const product = await extractProductFromTab(tab);
      collected.push(product);
    } catch (error) {
      failures.push(`${tab.title || tab.url || "Unknown tab"}: ${error.message || error}`);
    }
  }

  if (!collected.length) {
    throw new Error(`Could not collect any tabs. ${failures.slice(0, 2).join(" | ")}`);
  }

  const { products } = await getSavedProducts();
  const merged = mergeProductsByUrl(products, collected);
  await setSavedProducts(merged);

  $("previewCard").hidden = false;
  $("preview").textContent = JSON.stringify(collected[collected.length - 1], null, 2);

  const reviewTotal = collected.reduce((sum, product) => sum + (product.reviews || []).length, 0);
  const warningCount = collected.filter((product) => captureDiagnosticMessage(product)).length;
  const failureSuffix = failures.length ? ` ${failures.length} tab(s) skipped.` : "";
  const warningSuffix = warningCount ? ` ${warningCount} capture warning(s).` : "";
  setStatus(`Collected ${collected.length} tab(s), ${reviewTotal} visible review(s).${failureSuffix}${warningSuffix}`);
}


async function analyzeWorkspace() {
  const backendUrl = $("backendUrl").value.trim().replace(/\/$/, "") || DEFAULT_BACKEND;
  await chrome.storage.local.set({ backendUrl });

  const { products } = await getSavedProducts();
  if (!products.length) {
    throw new Error("Save at least one product first.");
  }

  setStatus("Analyzing saved workspace...");

  const response = await fetch(`${backendUrl}/api/v1/analyze-review-workspace`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      workspace_id: `extension_workspace_${Date.now()}`,
      source: "chrome_extension",
      output_language: "en",
      products
    })
  });

  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error || "Workspace analysis failed.");
  }

  lastWorkspaceAnalysis = body;
  $("analysisCard").hidden = false;
  renderWorkspaceAnalysis(body);
  $("analysisOutput").textContent = JSON.stringify({
    product_count: body.product_count,
    total_reviews: body.total_reviews,
    high_signal_review_count: body.high_signal_review_count,
    common_pain_points: body.common_pain_points,
    buyer_objections: body.buyer_objections,
    creative_angles: body.creative_angles,
    hooks: body.hooks
  }, null, 2);

  setStatus("Workspace analysis ready.");
}

async function clearSavedProducts() {
  await setSavedProducts([]);
  $("previewCard").hidden = true;
  $("analysisCard").hidden = true;
  $("preview").textContent = "";
  $("analysisOutput").textContent = "";
  const analysisSummary = $("analysisSummary");
  if (analysisSummary) {
    analysisSummary.innerHTML = "";
  }
  setStatus("Cleared saved products.");
}

function bind(id, handler) {
  $(id).addEventListener("click", async () => {
    try {
      await handler();
    } catch (error) {
      setStatus(error.message || String(error), true);
    }
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  bind("extractBtn", saveCurrentProduct);
  bind("collectTabsBtn", collectOpenTabs);
  bind("analyzeBtn", analyzeWorkspace);
  bind("copyInsightsBtn", copyInsights);
  bind("copyWorkspaceJsonBtn", copyWorkspaceJson);
  bind("openWorkspaceBtn", openInWebWorkspace);
  bind("clearBtn", clearSavedProducts);
  $("backendUrl").addEventListener("change", async () => {
    await chrome.storage.local.set({ backendUrl: $("backendUrl").value.trim() || DEFAULT_BACKEND });
  });
  await updateStats();
});
