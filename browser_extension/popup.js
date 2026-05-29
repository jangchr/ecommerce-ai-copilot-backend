const DEFAULT_BACKEND = "https://ecommerce-ai-copilot-backend.onrender.com";

function $(id) {
  return document.getElementById(id);
}

function setStatus(message, isError = false) {
  const node = $("status");
  node.textContent = message;
  node.style.color = isError ? "#b91c1c" : "#15803d";
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

async function updateStats() {
  const { products, backendUrl } = await getSavedProducts();
  $("backendUrl").value = backendUrl;
  $("savedCount").textContent = String(products.length);
  $("reviewCount").textContent = String(products.reduce((sum, product) => sum + (product.reviews || []).length, 0));
}

async function getActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tabs.length || !tabs[0].id) {
    throw new Error("No active tab found.");
  }
  return tabs[0];
}

async function extractCurrentProduct() {
  const tab = await getActiveTab();
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
    throw new Error("Could not extract product details from this page.");
  }
  return product;
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
  setStatus(`Saved: ${product.title || product.url}. Reviews: ${(product.reviews || []).length}`);
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

  $("analysisCard").hidden = false;
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
  bind("analyzeBtn", analyzeWorkspace);
  bind("clearBtn", clearSavedProducts);
  $("backendUrl").addEventListener("change", async () => {
    await chrome.storage.local.set({ backendUrl: $("backendUrl").value.trim() || DEFAULT_BACKEND });
  });
  await updateStats();
});
