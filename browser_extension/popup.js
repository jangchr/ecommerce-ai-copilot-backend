const DEFAULT_BACKEND = "https://ecommerce-ai-copilot-backend.onrender.com";
let lastWorkspaceAnalysis = null;
let popupLanguage = "en";

const POPUP_COPY = {
  en: {
    title: "Review Collector",
    subtitle: "Save visible product signals from the current tab and analyze high-signal buyer language.",
    visibleSampleTitle: "Visible-page sample",
    visibleSampleBody: "Collects visible product signals, reviews, and comments only. It does not bypass login, CAPTCHA, hidden review pages, or platform restrictions.",
    visibleSampleUse: "Use this for creative signals, buyer language, pain points, objections, and hooks, not full review statistics.",
    backendUrlLabel: "Backend URL",
    backendUrlHelper: "Use local backend for development: http://127.0.0.1:8001",
    saveCurrentProduct: "Save current product",
    collectOpenTabs: "Collect open tabs",
    autoCollectMoreReviews: "Auto collect more reviews",
    autoCollectMaxPagesLabel: "Max pages",
    collectingMoreReviews: "Auto collecting visible review pages...",
    backgroundCollectorDone: "Auto collected {pages} page(s), {added} new visible review(s), {duplicates} duplicate review(s) skipped, {total} saved review(s).",
    backgroundCollectorStopped: "Auto collector stopped: {reason}",
    repeatedReviewPageContent: "Later review pages repeated the same visible content, so collection stopped early.",
    repeatedCollectorUrl: "Next collector URL repeated, so collection stopped.",
    noAmazonAsin: "Could not find an Amazon ASIN on the current page.",
    couldNotCreateCollectorTab: "Could not create background collector tab.",
    analyzeSavedWorkspace: "Analyze saved workspace",
    clearSavedProducts: "Clear saved products",
    savedProducts: "Saved products",
    visibleReviews: "Visible reviews",
    sampleGuidanceTitle: "Sample expansion tips",
    sampleGuidanceIntro: "Current saved sample: {count} visible review(s). For stronger creative signals, open more useful review tabs, then click Collect open tabs.",
    sampleGuidanceLowStar: "Open low-star review pages to capture objections and pain points.",
    sampleGuidanceVerifiedPurchase: "Open verified-purchase review pages to capture more grounded buyer language.",
    sampleGuidanceVariants: "Open variant review pages for other colors, sizes, bundles, or formats.",
    sampleGuidanceCompetitors: "Open competitor product review pages to compare repeated pain points.",
    sampleGuidanceLoggedIn: "Open logged-in visible review pages if Amazon shows more content after sign-in.",
    sampleGuidanceCta: "After opening those tabs, use Collect open tabs to merge and deduplicate the sample.",
    readyStatus: "Ready.",
    currentCapture: "Current capture",
    workspaceAnalysis: "Workspace analysis",
    copyInsights: "Copy insights",
    copyWorkspaceJson: "Copy workspace JSON",
    openWebWorkspace: "Open in Web Workspace",
    rawResponse: "Raw response",
    products: "Products",
    totalReviews: "Total reviews",
    highSignal: "High-signal",
    topPainPoints: "Top pain points",
    buyerObjections: "Buyer objections",
    creativeAngles: "Creative angles",
    hooks: "Hooks",
    collectedProducts: "Collected products",
    noSignals: "No signals detected yet.",
    noRepeatedTheme: "No repeated theme detected yet.",
    noRepeatedSignals: "- No repeated signals detected yet.",
    noItems: "- No items generated yet.",
    noProducts: "- No products collected yet.",
    theme: "Theme",
    evidence: "Evidence",
    reviewSingular: "review",
    reviewPlural: "reviews",
    saveBeforeWebWorkspace: "Save or collect products before opening the web workspace.",
    couldNotOpenWebWorkspace: "Could not open web workspace tab.",
    openedWebWorkspace: "Opened workspace in web app.",
    analyzeBeforeCopy: "Analyze a workspace before copying insights.",
    copiedInsights: "Copied insights to clipboard.",
    insightsTitle: "CrossGrowth Review Workspace Insights",
    saveBeforeCopyJson: "Save or collect products before copying workspace JSON.",
    copiedWorkspaceJson: "Copied workspace JSON to clipboard.",
    signInRequired: "Amazon sign-in required. The extension only collects visible page content.",
    noVisibleReviews: "Product info captured. No visible reviews found. Scroll to reviews or open a visible review page.",
    visibleAmazonSample: "Visible Amazon review sample only; not the full review set.",
    noActiveTab: "No active tab found.",
    couldNotExtract: "Could not extract product details from this tab.",
    collectingCurrentTab: "Collecting current tab...",
    savedPrefix: "Saved",
    reviewsLabel: "Reviews",
    collectingOpenTabs: "Collecting open Amazon/TikTok tabs...",
    noCollectableTabs: "No Amazon or TikTok tabs found in this window.",
    couldNotCollectTabs: "Could not collect any tabs.",
    tabsSkipped: "tab(s) skipped.",
    captureWarnings: "capture warning(s).",
    collectedPrefix: "Collected",
    collectedTabsMerged: "Collected {tabs} tab(s), {added} new visible review(s), {duplicates} duplicate review(s) skipped, {total} saved review(s).",
    tabUnit: "tab(s)",
    visibleReviewUnit: "visible review(s)",
    saveFirst: "Save at least one product first.",
    analyzingWorkspace: "Analyzing saved workspace...",
    workspaceFailed: "Workspace analysis failed.",
    workspaceReady: "Workspace analysis ready.",
    cleared: "Cleared saved products.",
  },
  "zh-CN": {
    "title": "\u8bc4\u8bba\u91c7\u96c6\u5668",
    "subtitle": "\u4fdd\u5b58\u5f53\u524d\u9875\u9762\u53ef\u89c1\u7684\u5546\u54c1\u4fe1\u53f7\uff0c\u5e76\u5206\u6790\u9ad8\u4ef7\u503c\u4e70\u5bb6\u8bed\u8a00\u3002",
    "visibleSampleTitle": "\u4ec5\u91c7\u96c6\u5f53\u524d\u53ef\u89c1\u9875\u9762\u6837\u672c",
    "visibleSampleBody": "\u53ea\u91c7\u96c6\u9875\u9762\u4e0a\u5df2\u7ecf\u53ef\u89c1\u7684\u5546\u54c1\u4fe1\u53f7\u3001\u8bc4\u8bba\u548c\u7559\u8a00\u3002\u4e0d\u4f1a\u7ed5\u8fc7\u767b\u5f55\u3001\u9a8c\u8bc1\u7801\u3001\u9690\u85cf\u8bc4\u8bba\u9875\u6216\u5e73\u53f0\u9650\u5236\u3002",
    "visibleSampleUse": "\u9002\u5408\u63d0\u53d6\u521b\u610f\u4fe1\u53f7\u3001\u4e70\u5bb6\u539f\u8bdd\u3001\u75db\u70b9\u3001\u987e\u8651\u548c hook\uff0c\u4e0d\u9002\u5408\u5f53\u4f5c\u5b8c\u6574\u8bc4\u8bba\u7edf\u8ba1\u3002",
    "backendUrlLabel": "\u540e\u7aef\u5730\u5740",
    "backendUrlHelper": "\u672c\u5730\u5f00\u53d1\u4f7f\u7528\uff1ahttp://127.0.0.1:8001",
    "saveCurrentProduct": "\u4fdd\u5b58\u5f53\u524d\u5546\u54c1",
    "collectOpenTabs": "\u91c7\u96c6\u5df2\u6253\u5f00\u6807\u7b7e\u9875",
    "autoCollectMoreReviews": "\u81ea\u52a8\u91c7\u96c6\u66f4\u591a\u8bc4\u8bba",
    "autoCollectMaxPagesLabel": "\u6700\u5927\u9875\u6570",
    "collectingMoreReviews": "\u6b63\u5728\u81ea\u52a8\u91c7\u96c6\u53ef\u89c1\u8bc4\u8bba\u9875...",
    "backgroundCollectorDone": "\u5df2\u81ea\u52a8\u91c7\u96c6 {pages} \u9875\uff0c\u65b0\u589e {added} \u6761\u53ef\u89c1\u8bc4\u8bba\uff0c\u8df3\u8fc7 {duplicates} \u6761\u91cd\u590d\u8bc4\u8bba\uff0c\u5f53\u524d\u7d2f\u8ba1 {total} \u6761\u8bc4\u8bba\u3002",
    "backgroundCollectorStopped": "\u81ea\u52a8\u91c7\u96c6\u5df2\u505c\u6b62\uff1a{reason}",
    "repeatedReviewPageContent": "\u540e\u7eed\u8bc4\u8bba\u9875\u8fd4\u56de\u4e86\u76f8\u540c\u7684\u53ef\u89c1\u5185\u5bb9\uff0c\u5df2\u63d0\u524d\u505c\u6b62\u91c7\u96c6\u3002",
    "repeatedCollectorUrl": "\u4e0b\u4e00\u4e2a\u91c7\u96c6 URL \u91cd\u590d\uff0c\u5df2\u505c\u6b62\u7ee7\u7eed\u91c7\u96c6\u3002",
    "noAmazonAsin": "\u65e0\u6cd5\u5728\u5f53\u524d\u9875\u9762\u627e\u5230 Amazon ASIN\u3002",
    "couldNotCreateCollectorTab": "\u65e0\u6cd5\u521b\u5efa\u540e\u53f0\u91c7\u96c6\u6807\u7b7e\u9875\u3002",
    "analyzeSavedWorkspace": "\u5206\u6790\u5df2\u4fdd\u5b58\u5de5\u4f5c\u533a",
    "clearSavedProducts": "\u6e05\u7a7a\u5df2\u4fdd\u5b58\u5546\u54c1",
    "savedProducts": "\u5df2\u4fdd\u5b58\u5546\u54c1",
    "visibleReviews": "\u53ef\u89c1\u8bc4\u8bba",
    "sampleGuidanceTitle": "\u6837\u672c\u589e\u5f3a\u5efa\u8bae",
    "sampleGuidanceIntro": "\u5f53\u524d\u5df2\u4fdd\u5b58\u6837\u672c\uff1a{count} \u6761\u53ef\u89c1\u8bc4\u8bba\u3002\u4e3a\u4e86\u83b7\u5f97\u66f4\u5f3a\u7684\u521b\u610f\u4fe1\u53f7\uff0c\u5efa\u8bae\u5148\u6253\u5f00\u66f4\u591a\u6709\u7528\u7684\u8bc4\u8bba\u6807\u7b7e\u9875\uff0c\u7136\u540e\u70b9\u51fb\u201c\u91c7\u96c6\u5df2\u6253\u5f00\u6807\u7b7e\u9875\u201d\u5408\u5e76\u3002",
    "sampleGuidanceLowStar": "\u6253\u5f00\u4f4e\u661f\u8bc4\u8bba\u9875\uff0c\u6355\u6349\u8d2d\u4e70\u987e\u8651\u548c\u75db\u70b9\u3002",
    "sampleGuidanceVerifiedPurchase": "\u6253\u5f00\u5df2\u786e\u8ba4\u8d2d\u4e70\u8bc4\u8bba\u9875\uff0c\u83b7\u5f97\u66f4\u624e\u5b9e\u7684\u4e70\u5bb6\u539f\u8bdd\u3002",
    "sampleGuidanceVariants": "\u6253\u5f00\u5176\u4ed6\u989c\u8272\u3001\u5c3a\u7801\u3001\u7ec4\u5408\u6216\u89c4\u683c\u7684\u53d8\u4f53\u8bc4\u8bba\u9875\u3002",
    "sampleGuidanceCompetitors": "\u6253\u5f00\u7ade\u54c1\u8bc4\u8bba\u9875\uff0c\u5bf9\u6bd4\u91cd\u590d\u51fa\u73b0\u7684\u75db\u70b9\u548c\u5356\u70b9\u7f3a\u53e3\u3002",
    "sampleGuidanceLoggedIn": "\u5982\u679c Amazon \u767b\u5f55\u540e\u663e\u793a\u66f4\u591a\u5185\u5bb9\uff0c\u53ef\u4ee5\u6253\u5f00\u90a3\u4e9b\u5df2\u767b\u5f55\u53ef\u89c1\u8bc4\u8bba\u9875\u3002",
    "sampleGuidanceCta": "\u6253\u5f00\u8fd9\u4e9b\u6807\u7b7e\u9875\u540e\uff0c\u4f7f\u7528\u201c\u91c7\u96c6\u5df2\u6253\u5f00\u6807\u7b7e\u9875\u201d\u6765\u5408\u5e76\u5e76\u53bb\u91cd\u6837\u672c\u3002",
    "readyStatus": "\u51c6\u5907\u597d\u4e86\u3002",
    "currentCapture": "\u5f53\u524d\u91c7\u96c6\u7ed3\u679c",
    "workspaceAnalysis": "\u5de5\u4f5c\u533a\u5206\u6790",
    "copyInsights": "\u590d\u5236\u6d1e\u5bdf",
    "copyWorkspaceJson": "\u590d\u5236\u5de5\u4f5c\u533a JSON",
    "openWebWorkspace": "\u5728 Web Workspace \u6253\u5f00",
    "rawResponse": "\u539f\u59cb\u54cd\u5e94",
    "products": "\u5546\u54c1",
    "totalReviews": "\u8bc4\u8bba\u603b\u6570",
    "highSignal": "\u9ad8\u4fe1\u53f7",
    "topPainPoints": "\u4e3b\u8981\u75db\u70b9",
    "buyerObjections": "\u8d2d\u4e70\u987e\u8651",
    "creativeAngles": "\u521b\u610f\u89d2\u5ea6",
    "hooks": "Hooks",
    "collectedProducts": "\u5df2\u91c7\u96c6\u5546\u54c1",
    "noSignals": "\u8fd8\u6ca1\u6709\u68c0\u6d4b\u5230\u4fe1\u53f7\u3002",
    "noRepeatedTheme": "\u8fd8\u6ca1\u6709\u68c0\u6d4b\u5230\u91cd\u590d\u4e3b\u9898\u3002",
    "noRepeatedSignals": "- \u8fd8\u6ca1\u6709\u68c0\u6d4b\u5230\u91cd\u590d\u4fe1\u53f7\u3002",
    "noItems": "- \u8fd8\u6ca1\u6709\u751f\u6210\u5185\u5bb9\u3002",
    "noProducts": "- \u8fd8\u6ca1\u6709\u91c7\u96c6\u5546\u54c1\u3002",
    "theme": "\u4e3b\u9898",
    "evidence": "\u8bc1\u636e",
    "reviewSingular": "\u6761\u8bc4\u8bba",
    "reviewPlural": "\u6761\u8bc4\u8bba",
    "saveBeforeWebWorkspace": "\u8bf7\u5148\u4fdd\u5b58\u6216\u91c7\u96c6\u5546\u54c1\uff0c\u518d\u6253\u5f00 Web Workspace\u3002",
    "couldNotOpenWebWorkspace": "\u65e0\u6cd5\u6253\u5f00 Web Workspace \u6807\u7b7e\u9875\u3002",
    "openedWebWorkspace": "\u5df2\u5728 Web \u5e94\u7528\u4e2d\u6253\u5f00\u5de5\u4f5c\u533a\u3002",
    "analyzeBeforeCopy": "\u8bf7\u5148\u5206\u6790\u5de5\u4f5c\u533a\uff0c\u518d\u590d\u5236\u6d1e\u5bdf\u3002",
    "copiedInsights": "\u5df2\u590d\u5236\u6d1e\u5bdf\u3002",
    "insightsTitle": "CrossGrowth \u8bc4\u8bba\u5de5\u4f5c\u533a\u6d1e\u5bdf",
    "saveBeforeCopyJson": "\u8bf7\u5148\u4fdd\u5b58\u6216\u91c7\u96c6\u5546\u54c1\uff0c\u518d\u590d\u5236\u5de5\u4f5c\u533a JSON\u3002",
    "copiedWorkspaceJson": "\u5df2\u590d\u5236\u5de5\u4f5c\u533a JSON\u3002",
    "signInRequired": "Amazon \u9700\u8981\u767b\u5f55\u3002\u63d2\u4ef6\u53ea\u91c7\u96c6\u5f53\u524d\u9875\u9762\u53ef\u89c1\u5185\u5bb9\u3002",
    "noVisibleReviews": "\u5df2\u91c7\u96c6\u5546\u54c1\u4fe1\u606f\uff0c\u4f46\u672a\u53d1\u73b0\u53ef\u89c1\u8bc4\u8bba\u3002\u8bf7\u6eda\u52a8\u5230\u8bc4\u8bba\u533a\uff0c\u6216\u6253\u5f00\u53ef\u89c1\u8bc4\u8bba\u9875\u3002",
    "visibleAmazonSample": "\u4ec5\u4e3a Amazon \u53ef\u89c1\u8bc4\u8bba\u6837\u672c\uff0c\u4e0d\u4ee3\u8868\u5b8c\u6574\u8bc4\u8bba\u96c6\u3002",
    "noActiveTab": "\u6ca1\u6709\u627e\u5230\u5f53\u524d\u6d3b\u52a8\u6807\u7b7e\u9875\u3002",
    "couldNotExtract": "\u65e0\u6cd5\u4ece\u5f53\u524d\u6807\u7b7e\u9875\u63d0\u53d6\u5546\u54c1\u8be6\u60c5\u3002",
    "collectingCurrentTab": "\u6b63\u5728\u91c7\u96c6\u5f53\u524d\u6807\u7b7e\u9875...",
    "savedPrefix": "\u5df2\u4fdd\u5b58",
    "reviewsLabel": "\u8bc4\u8bba",
    "collectingOpenTabs": "\u6b63\u5728\u91c7\u96c6\u5df2\u6253\u5f00\u7684 Amazon/TikTok \u6807\u7b7e\u9875...",
    "noCollectableTabs": "\u5f53\u524d\u7a97\u53e3\u6ca1\u6709\u627e\u5230 Amazon \u6216 TikTok \u6807\u7b7e\u9875\u3002",
    "couldNotCollectTabs": "\u672a\u80fd\u91c7\u96c6\u4efb\u4f55\u6807\u7b7e\u9875\u3002",
    "tabsSkipped": "\u4e2a\u6807\u7b7e\u9875\u5df2\u8df3\u8fc7\u3002",
    "captureWarnings": "\u4e2a\u91c7\u96c6\u63d0\u793a\u3002",
    "collectedPrefix": "\u5df2\u91c7\u96c6",
    "collectedTabsMerged": "\u5df2\u91c7\u96c6 {tabs} \u4e2a\u6807\u7b7e\u9875\uff0c\u65b0\u589e {added} \u6761\u53ef\u89c1\u8bc4\u8bba\uff0c\u8df3\u8fc7 {duplicates} \u6761\u91cd\u590d\u8bc4\u8bba\uff0c\u5f53\u524d\u7d2f\u8ba1 {total} \u6761\u8bc4\u8bba\u3002",
    "tabUnit": "\u4e2a\u6807\u7b7e\u9875",
    "visibleReviewUnit": "\u6761\u53ef\u89c1\u8bc4\u8bba",
    "saveFirst": "\u8bf7\u5148\u4fdd\u5b58\u81f3\u5c11\u4e00\u4e2a\u5546\u54c1\u3002",
    "analyzingWorkspace": "\u6b63\u5728\u5206\u6790\u5df2\u4fdd\u5b58\u5de5\u4f5c\u533a...",
    "workspaceFailed": "\u5de5\u4f5c\u533a\u5206\u6790\u5931\u8d25\u3002",
    "workspaceReady": "\u5de5\u4f5c\u533a\u5206\u6790\u5b8c\u6210\u3002",
    "cleared": "\u5df2\u6e05\u7a7a\u4fdd\u5b58\u7684\u5546\u54c1\u3002"
  }
};

function tPopup(key) {
  return POPUP_COPY[popupLanguage]?.[key] || POPUP_COPY.en[key] || key;
}

function popupOutputLanguage() {
  return popupLanguage === "zh-CN" ? "zh-CN" : "en";
}


const POPUP_THEME_LABELS = {
  en: {
    "price / value concern": "price / value concern",
    "taste / flavor concern": "taste / flavor concern",
    "size / quantity mismatch": "size / quantity mismatch",
    "size / fit issue": "size / fit issue",
    "durability concern": "durability concern",
    "leak / mess risk": "leak / mess risk",
    "hard to clean": "hard to clean",
    "space constraint": "space constraint",
    "quality consistency concern": "quality consistency concern",
    "quantity / size uncertainty": "quantity / size uncertainty",
    "tradeoff / hesitation": "tradeoff / hesitation",
    "expectation mismatch": "expectation mismatch",
    "liked signal: great": "liked signal: great",
    "liked signal: love": "liked signal: love"
  },
  "zh-CN": {
    "price / value concern": "\u4ef7\u683c / \u4ef7\u503c\u987e\u8651",
    "taste / flavor concern": "\u5473\u9053 / \u98ce\u5473\u987e\u8651",
    "size / quantity mismatch": "\u89c4\u683c / \u6570\u91cf\u4e0d\u4e00\u81f4",
    "size / fit issue": "\u5c3a\u5bf8 / \u9002\u914d\u95ee\u9898",
    "durability concern": "\u8010\u7528\u6027\u987e\u8651",
    "leak / mess risk": "\u6f0f\u6db2 / \u810f\u4e71\u98ce\u9669",
    "hard to clean": "\u6e05\u6d01\u56f0\u96be",
    "space constraint": "\u7a7a\u95f4\u9650\u5236",
    "quality consistency concern": "\u54c1\u8d28\u7a33\u5b9a\u6027\u987e\u8651",
    "quantity / size uncertainty": "\u6570\u91cf / \u89c4\u683c\u4e0d\u786e\u5b9a",
    "tradeoff / hesitation": "\u53d6\u820d / \u72b9\u8c6b",
    "expectation mismatch": "\u9884\u671f\u4e0d\u4e00\u81f4",
    "liked signal: great": "\u6b63\u5411\u4fe1\u53f7\uff1agreat",
    "liked signal: love": "\u6b63\u5411\u4fe1\u53f7\uff1alove"
  }
};

function popupThemeLabel(label) {
  const normalized = String(label || "").trim().toLowerCase();
  if (!normalized) return tPopup("theme");
  return POPUP_THEME_LABELS[popupLanguage]?.[normalized]
    || POPUP_THEME_LABELS.en[normalized]
    || label;
}

function applyPopupLanguage() {
  document.documentElement.lang = popupOutputLanguage();
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const key = node.getAttribute("data-i18n");
    node.textContent = tPopup(key);
  });
  const englishBtn = $("popupLanguageEnglish");
  const chineseBtn = $("popupLanguageChinese");
  if (englishBtn) englishBtn.classList.toggle("active", popupLanguage === "en");
  if (chineseBtn) chineseBtn.classList.toggle("active", popupLanguage === "zh-CN");
}

async function setPopupLanguage(language) {
  popupLanguage = language === "zh-CN" ? "zh-CN" : "en";
  await chrome.storage.local.set({ popupLanguage });
  applyPopupLanguage();
  await updateStats();
  if (lastWorkspaceAnalysis) {
    renderWorkspaceAnalysis(lastWorkspaceAnalysis);
  }
}


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

function listItems(values, emptyMessage = tPopup("noSignals")) {
  const items = (values || []).filter(Boolean).slice(0, 6);
  if (!items.length) {
    return `<div class="empty">${escapeHTML(emptyMessage)}</div>`;
  }
  return `<ul>${items.map((value) => `<li>${escapeHTML(value)}</li>`).join("")}</ul>`;
}

function themeItems(themes, emptyMessage = tPopup("noRepeatedTheme")) {
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
    return `<li><strong>${escapeHTML(popupThemeLabel(theme.label || tPopup("theme")))}</strong>${count}${quotes}</li>`;
  }).join("")}</ul>`;
}

function renderWorkspaceAnalysis(body) {
  const summary = $("analysisSummary");
  if (!summary) return;

  summary.innerHTML = `
    <div class="metric-grid">
      <div class="metric-card">
        <span>${escapeHTML(tPopup("products"))}</span>
        <strong>${escapeHTML(body.product_count ?? 0)}</strong>
      </div>
      <div class="metric-card">
        <span>${escapeHTML(tPopup("totalReviews"))}</span>
        <strong>${escapeHTML(body.total_reviews ?? 0)}</strong>
      </div>
      <div class="metric-card">
        <span>${escapeHTML(tPopup("highSignal"))}</span>
        <strong>${escapeHTML(body.high_signal_review_count ?? 0)}</strong>
      </div>
    </div>

    <div class="insight-section">
      <h3>${escapeHTML(tPopup("topPainPoints"))}</h3>
      ${themeItems(body.common_pain_points)}
    </div>

    <div class="insight-section">
      <h3>${escapeHTML(tPopup("buyerObjections"))}</h3>
      ${themeItems(body.buyer_objections)}
    </div>

    <div class="insight-section">
      <h3>${escapeHTML(tPopup("creativeAngles"))}</h3>
      ${listItems(body.creative_angles)}
    </div>

    <div class="insight-section">
      <h3>${escapeHTML(tPopup("hooks"))}</h3>
      ${listItems(body.hooks)}
    </div>
  `;
}



function compactThemeLines(title, themes) {
  const rows = [`${title}:`];
  const items = (themes || []).slice(0, 6);
  if (!items.length) {
    rows.push(tPopup("noRepeatedSignals"));
    return rows;
  }

  for (const theme of items) {
    const count = theme.evidence_count ? ` (${theme.evidence_count})` : "";
    rows.push(`- ${popupThemeLabel(theme.label || tPopup("theme"))}${count}`);
    for (const quote of (theme.evidence_quotes || []).slice(0, 2)) {
      rows.push(`  ${tPopup("evidence")}: ${quote}`);
    }
  }
  return rows;
}

function compactListLines(title, values) {
  const rows = [`${title}:`];
  const items = (values || []).filter(Boolean).slice(0, 8);
  if (!items.length) {
    rows.push(tPopup("noItems"));
    return rows;
  }
  for (const item of items) {
    rows.push(`- ${item}`);
  }
  return rows;
}

function compactProductLines(products) {
  const rows = [`${tPopup("collectedProducts")}:`];
  const items = products || [];
  if (!items.length) {
    rows.push(tPopup("noProducts"));
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
    output_language: popupOutputLanguage(),
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
    throw new Error(tPopup("saveBeforeWebWorkspace"));
  }

  const payload = buildWorkspacePayload(products);
  const payloadJson = JSON.stringify(payload);
  const targetUrl = `${backendUrl}/?extension_workspace=1`;

  const tab = await chrome.tabs.create({ url: targetUrl, active: true });
  if (!tab.id) {
    throw new Error(tPopup("couldNotOpenWebWorkspace"));
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

  setStatus(tPopup("openedWebWorkspace"));
}


async function copyInsights() {
  if (!lastWorkspaceAnalysis) {
    throw new Error(tPopup("analyzeBeforeCopy"));
  }

  const { products } = await getSavedProducts();
  const body = lastWorkspaceAnalysis;

  const lines = [
    tPopup("insightsTitle"),
    "",
    `${tPopup("products")}: ${body.product_count ?? 0}`,
    `${tPopup("totalReviews")}: ${body.total_reviews ?? 0}`,
    `${tPopup("highSignal")}: ${body.high_signal_review_count ?? 0}`,
    "",
    ...compactProductLines(products),
    "",
    ...compactThemeLines(tPopup("topPainPoints"), body.common_pain_points),
    "",
    ...compactThemeLines(tPopup("buyerObjections"), body.buyer_objections),
    "",
    ...compactListLines(tPopup("creativeAngles"), body.creative_angles),
    "",
    ...compactListLines(tPopup("hooks"), body.hooks)
  ];

  await copyTextToClipboard(lines.join("\n"));
  setStatus(tPopup("copiedInsights"));
}

async function copyWorkspaceJson() {
  const { products } = await getSavedProducts();
  if (!products.length) {
    throw new Error(tPopup("saveBeforeCopyJson"));
  }

  await copyTextToClipboard(JSON.stringify(buildWorkspacePayload(products), null, 2));
  setStatus(tPopup("copiedWorkspaceJson"));
}


async function getSavedProducts() {
  const result = await chrome.storage.local.get(["workspaceProducts", "backendUrl", "popupLanguage", "autoCollectMaxPages"]);
  return {
    products: result.workspaceProducts || [],
    backendUrl: result.backendUrl || DEFAULT_BACKEND,
    popupLanguage: result.popupLanguage || "en",
    autoCollectMaxPages: result.autoCollectMaxPages || "3"
  };
}

async function setSavedProducts(products) {
  await chrome.storage.local.set({ workspaceProducts: products });
  await updateStats();
}


function shortProductTitle(product) {
  const rawTitle = String(product?.title || product?.url || "Untitled product").trim();
  const title = cleanCollectedProductTitle(rawTitle) || rawTitle || "Untitled product";
  return title.length > 86 ? `${title.slice(0, 83)}...` : title;
}

function captureDiagnosticMessage(product) {
  const metadata = product?.metadata || {};
  const status = metadata.review_visibility_status;

  if (metadata.sign_in_required || status === "sign_in_required") {
    return tPopup("signInRequired");
  }

  if (
    status === "no_visible_reviews_on_product_page" ||
    status === "no_visible_reviews_on_reviews_page" ||
    status === "no_visible_reviews"
  ) {
    return tPopup("noVisibleReviews");
  }

  if (
    product?.platform === "amazon" &&
    metadata.source_scope === "visible_page_sample" &&
    status === "visible_reviews_found"
  ) {
    return tPopup("visibleAmazonSample");
  }

  return "";
}

function productSourceLabel(product) {
  const platform = String(product?.platform || "web").toLowerCase();
  const reviewCount = (product?.reviews || []).length;
  const reviewLabel = reviewCount === 1 ? tPopup("reviewSingular") : tPopup("reviewPlural");
  return `${platform} - ${reviewCount} ${reviewLabel}`;
}

const SAMPLE_GUIDANCE_REVIEW_THRESHOLD = 50;

function totalSavedReviewCount(products) {
  return (products || []).reduce((sum, product) => sum + (product?.reviews || []).length, 0);
}

function renderSampleGuidance(products) {
  const card = $("sampleGuidanceCard");
  const intro = $("sampleGuidanceIntro");
  const list = $("sampleGuidanceList");
  const cta = $("sampleGuidanceCta");

  if (!card || !intro || !list || !cta) return;

  const reviewCount = totalSavedReviewCount(products);
  const shouldShow = Boolean((products || []).length) && reviewCount < SAMPLE_GUIDANCE_REVIEW_THRESHOLD;
  card.hidden = !shouldShow;

  if (!shouldShow) {
    intro.textContent = "";
    list.innerHTML = "";
    cta.textContent = "";
    return;
  }

  intro.textContent = tPopup("sampleGuidanceIntro").replace("{count}", String(reviewCount));
  const items = [
    "sampleGuidanceLowStar",
    "sampleGuidanceVerifiedPurchase",
    "sampleGuidanceVariants",
    "sampleGuidanceCompetitors",
    "sampleGuidanceLoggedIn"
  ];

  list.innerHTML = items.map((key) => `<li>${escapeHTML(tPopup(key))}</li>`).join("");
  cta.textContent = tPopup("sampleGuidanceCta");
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
    <div class="collected-header">${escapeHTML(tPopup("collectedProducts"))}</div>
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
  const { products, backendUrl, popupLanguage: savedLanguage, autoCollectMaxPages } = await getSavedProducts();
  popupLanguage = savedLanguage === "zh-CN" ? "zh-CN" : "en";
  applyPopupLanguage();
  $("backendUrl").value = backendUrl;
  const maxPagesSelect = $("autoCollectMaxPages");
  if (maxPagesSelect) {
    maxPagesSelect.value = String(autoCollectMaxPages || "3");
  }
  const totalReviews = totalSavedReviewCount(products);
  $("savedCount").textContent = String(products.length);
  $("reviewCount").textContent = String(totalReviews);
  renderSavedProducts(products);
  renderSampleGuidance(products);
}

async function getActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tabs.length || !tabs[0].id) {
    throw new Error(tPopup("noActiveTab"));
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
    throw new Error(tPopup("couldNotExtract"));
  }
  return product;
}

function cleanCollectedProductTitle(value) {
  return String(value || "")
    .replace(/^[\s\S]{0,120}(?:Customer reviews?|\u4e70\u5bb6\u8bc4\u8bba)\s*[:?]\s*/i, "")
    .replace(/^Amazon(?:\.[^:?\s]+)?[:?]\s*/i, "")
    .replace(/^(?:Customer reviews?|\u4e70\u5bb6\u8bc4\u8bba)\s*[:?]?\s*/i, "")
    .replace(/\s+/g, " ")
    .trim();
}

function cleanCollectedReviewText(value) {
  return String(value || "")
    .replace(/<img[^>]*>/gi, " ")
    .replace(/Translate\s*review\s*to\s*English/gi, " ")
    .replace(/Thank\s*you\s*for\s*your\s*feedback/gi, " ")
    .replace(/Sorry,\s*there\s*was\s*an\s*error/gi, " ")
    .replace(/More\s*Hide/gi, " ")
    .replace(/Helpful/gi, " ")
    .replace(/Report/gi, " ")
    .replace(/More/gi, " ")
    .replace(/Hide/gi, " ")
    .replace(/Close/gi, " ")
    .replace(/One\s+person\s+found\s+this(?:\s+helpful)?/gi, " ")
    .replace(/\d+\s+people\s+found\s+this(?:\s+helpful)?/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeCollectedProductForMerge(product) {
  if (!product) return product;

  return {
    ...product,
    title: cleanCollectedProductTitle(product.title || product.url || ""),
    reviews: (product.reviews || [])
      .map((review) => ({
        ...review,
        text: cleanCollectedReviewText(review.text || "")
      }))
      .filter((review) => review.text)
  };
}

function normalizeReviewIdentityText(value) {
  return cleanCollectedReviewText(value)
    .toLowerCase()
    .replace(/[^a-z0-9\u3040-\u30ff\u3400-\u9fff]+/g, "")
    .trim();
}

function reviewIdentityKey(review) {
  const text = normalizeReviewIdentityText(review?.text || "");
  if (!text) return "";
  const rating = String(review?.rating || "").trim().toLowerCase();
  return `${rating}|${text.slice(0, 320)}`;
}

function canonicalProductUrl(value) {
  try {
    const url = new URL(String(value || ""));
    url.hash = "";
    url.search = "";
    return url.href.replace(/\/$/, "");
  } catch (error) {
    return String(value || "").split("#")[0].split("?")[0].replace(/\/$/, "");
  }
}

function productIdentityKey(product) {
  const asin = String(product?.asin || product?.metadata?.asin || "").trim().toUpperCase();
  if (asin) return `asin:${asin}`;

  const url = canonicalProductUrl(product?.url || "");
  if (url) return `url:${url}`;

  const title = String(product?.title || "").trim().toLowerCase();
  const platform = String(product?.platform || "web").trim().toLowerCase();
  return `${platform}:${title}`;
}

function mergeReviewLists(existingReviews = [], newReviews = []) {
  const seen = new Set();
  const merged = [];
  let added = 0;
  let duplicates = 0;

  for (const review of existingReviews || []) {
    const key = reviewIdentityKey(review);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    merged.push(review);
  }

  for (const review of newReviews || []) {
    const key = reviewIdentityKey(review);
    if (!key) continue;

    if (seen.has(key)) {
      duplicates += 1;
      continue;
    }

    seen.add(key);
    merged.push(review);
    added += 1;
  }

  return { reviews: merged, added, duplicates };
}

function mergeProductsByUrlWithStats(existingProducts, newProducts) {
  const byKey = new Map();

  for (const product of existingProducts || []) {
    if (!product) continue;
    const normalizedProduct = normalizeCollectedProductForMerge(product);
    const key = productIdentityKey(normalizedProduct);
    if (!key) continue;
    byKey.set(key, {
      ...normalizedProduct,
      reviews: mergeReviewLists([], normalizedProduct.reviews || []).reviews
    });
  }

  let addedReviews = 0;
  let duplicateReviews = 0;
  let addedProducts = 0;
  let updatedProducts = 0;

  for (const product of newProducts || []) {
    if (!product) continue;
    const normalizedProduct = normalizeCollectedProductForMerge(product);
    const key = productIdentityKey(normalizedProduct);
    if (!key) continue;

    const incomingReviews = normalizedProduct.reviews || [];
    const existing = byKey.get(key);

    if (!existing) {
      const uniqueIncoming = mergeReviewLists([], incomingReviews);
      byKey.set(key, {
        ...normalizedProduct,
        reviews: uniqueIncoming.reviews
      });
      addedProducts += 1;
      addedReviews += uniqueIncoming.added;
      duplicateReviews += uniqueIncoming.duplicates;
      continue;
    }

    const mergedReviews = mergeReviewLists(existing.reviews || [], incomingReviews);
    byKey.set(key, {
      ...existing,
      ...normalizedProduct,
      url: existing.url || normalizedProduct.url,
      title: cleanCollectedProductTitle(existing.title || normalizedProduct.title || normalizedProduct.url || ""),
      asin: existing.asin || normalizedProduct.asin,
      reviews: mergedReviews.reviews,
      metadata: {
        ...(existing.metadata || {}),
        ...(normalizedProduct.metadata || {}),
        merged_visible_review_pages: true
      }
    });

    updatedProducts += 1;
    addedReviews += mergedReviews.added;
    duplicateReviews += mergedReviews.duplicates;
  }

  const products = Array.from(byKey.values());
  return {
    products,
    stats: {
      addedReviews,
      duplicateReviews,
      addedProducts,
      updatedProducts,
      totalReviews: products.reduce((sum, product) => sum + (product.reviews || []).length, 0)
    }
  };
}

function mergeProductsByUrl(existingProducts, newProducts) {
  return mergeProductsByUrlWithStats(existingProducts, newProducts).products;
}

async function extractCurrentProduct() {
  const tab = await getActiveTab();
  return extractProductFromTab(tab);
}

async function saveCurrentProduct() {
  setStatus(tPopup("collectingCurrentTab"));
  const product = await extractCurrentProduct();
  const { products } = await getSavedProducts();

  const deduped = products.filter((item) => item.url !== product.url);
  deduped.push(product);

  await setSavedProducts(deduped);
  $("previewCard").hidden = false;
  $("preview").textContent = JSON.stringify(product, null, 2);
  const diagnostic = captureDiagnosticMessage(product);
  const diagnosticSuffix = diagnostic ? ` ${diagnostic}` : "";
  setStatus(`${tPopup("savedPrefix")}: ${product.title || product.url}. ${tPopup("reviewsLabel")}: ${(product.reviews || []).length}.${diagnosticSuffix}`);
}


function amazonAsinFromProduct(product) {
  const explicit = String(product?.asin || product?.metadata?.asin || "").trim().toUpperCase();
  if (explicit) return explicit;

  const url = String(product?.url || "");
  const match = url.match(/\/(?:dp|gp\/product|product-reviews)\/([A-Z0-9]{10})/i);
  return match ? match[1].toUpperCase() : "";
}

function isAmazonReviewPageUrl(value) {
  try {
    const url = new URL(String(value || ""));
    return url.hostname.toLowerCase().includes("amazon.") && url.pathname.toLowerCase().includes("/product-reviews/");
  } catch (error) {
    return false;
  }
}

function amazonReviewCollectorStartUrl(product, activeTabUrl) {
  if (isAmazonReviewPageUrl(activeTabUrl)) {
    return String(activeTabUrl || "");
  }

  return amazonReviewPageUrlFor(product, 1, activeTabUrl);
}

function amazonReviewPageUrlFor(product, pageNumber = 1, sourceUrl = "") {
  const asin = amazonAsinFromProduct(product);
  if (!asin) return "";

  const rawUrl = String(product?.url || sourceUrl || "");
  let parsed;
  try {
    parsed = new URL(rawUrl);
  } catch (error) {
    return "";
  }

  const languagePrefix = parsed.pathname.includes("/-/zh/") ? "/-/zh" : "";
  const reviewUrl = new URL(`${parsed.origin}${languagePrefix}/product-reviews/${asin}`);
  reviewUrl.searchParams.set("reviewerType", "all_reviews");
  reviewUrl.searchParams.set("pageNumber", String(pageNumber));
  return reviewUrl.href;
}

function amazonReviewPageNumberFromUrl(value) {
  try {
    const url = new URL(String(value || ""));
    const pageNumber = Number(url.searchParams.get("pageNumber") || "0") || 0;
    return pageNumber > 0 ? pageNumber : 1;
  } catch (error) {
    return 1;
  }
}

function nextSequentialAmazonReviewUrl(product, currentUrl, nextPageNumber) {
  try {
    const url = new URL(String(currentUrl || ""));
    if (url.hostname.toLowerCase().includes("amazon.") && url.pathname.toLowerCase().includes("/product-reviews/")) {
      url.searchParams.set("pageNumber", String(nextPageNumber));
      url.searchParams.delete("nextPageToken");
      return url.href;
    }
  } catch (error) {
    // Fall back to product-based review URL below.
  }

  return amazonReviewPageUrlFor(product, nextPageNumber, currentUrl);
}

function reviewPageSignatureFromProduct(product) {
  const keys = (product?.reviews || [])
    .map((review) => reviewIdentityKey(review))
    .filter(Boolean)
    .sort();

  return keys.join("||");
}

function backgroundCollectorStopReason(product) {
  const metadata = product?.metadata || {};
  if (metadata.sign_in_required || metadata.review_visibility_status === "sign_in_required") {
    return tPopup("signInRequired");
  }

  if (!(product?.reviews || []).length) {
    return tPopup("noVisibleReviews");
  }

  return "";
}

function readAutoCollectMaxPages() {
  const rawValue = Number($("autoCollectMaxPages")?.value || 3);
  return [3, 5, 10].includes(rawValue) ? rawValue : 3;
}

function sameCollectorUrl(left, right) {
  try {
    const leftUrl = new URL(String(left || ""));
    const rightUrl = new URL(String(right || ""));
    leftUrl.hash = "";
    rightUrl.hash = "";
    return leftUrl.href === rightUrl.href;
  } catch (error) {
    return String(left || "") === String(right || "");
  }
}

function isAmazonLoadMoreCollectorUrl(value) {
  try {
    const url = new URL(String(value || ""));
    return url.hostname.toLowerCase().includes("amazon.")
      && url.pathname.toLowerCase().includes("/product-reviews/")
      && url.href.toLowerCase().includes("cm_cr_arp_d_paging_btm");
  } catch (error) {
    return String(value || "").toLowerCase().includes("cm_cr_arp_d_paging_btm");
  }
}

function chooseNextCollectorUrl(currentUrl, nextFromPage, fallbackNextUrl, visitedCollectorUrls) {
  const nextUrl = String(nextFromPage || "").trim();
  const fallbackUrl = String(fallbackNextUrl || "").trim();

  if (nextUrl && !sameCollectorUrl(nextUrl, currentUrl) && !visitedCollectorUrls.has(nextUrl)) {
    return {
      selected_url: nextUrl,
      ignored_next_review_page_url: "",
      source: "next_review_page_url"
    };
  }

  const ignored = nextUrl ? nextUrl : "";

  if (isAmazonLoadMoreCollectorUrl(currentUrl) && ignored) {
    return {
      selected_url: "",
      ignored_next_review_page_url: ignored,
      source: "load_more_terminal"
    };
  }

  if (fallbackUrl && !sameCollectorUrl(fallbackUrl, currentUrl) && !visitedCollectorUrls.has(fallbackUrl)) {
    return {
      selected_url: fallbackUrl,
      ignored_next_review_page_url: ignored,
      source: "fallback_next_url"
    };
  }

  return {
    selected_url: "",
    ignored_next_review_page_url: ignored,
    source: "none"
  };
}

function shouldClickAmazonLoadMore(nextChoice) {
  return nextChoice?.source === "next_review_page_url"
    && isAmazonLoadMoreCollectorUrl(nextChoice?.selected_url);
}

async function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function clickAmazonReviewLoadMoreInTab(tabId) {
  const results = await chrome.scripting.executeScript({
    target: { tabId },
    func: () => {
      function cleanText(value) {
        return String(value || "").replace(/\s+/g, " ").trim();
      }

      function currentAmazonAsin() {
        const match = location.href.match(/\/(?:dp|gp\/product|product-reviews)\/([A-Z0-9]{10})/i);
        return match ? match[1].toUpperCase() : "";
      }

      function hrefAsin(value) {
        const match = String(value || "").match(/\/(?:dp|gp\/product|product-reviews)\/([A-Z0-9]{10})/i);
        return match ? match[1].toUpperCase() : "";
      }

      function absoluteHref(value) {
        try {
          return new URL(value, location.href).href;
        } catch (error) {
          return "";
        }
      }

      function visibleReviewCount() {
        return Array.from(document.querySelectorAll("[data-hook='review'], [id^='customer_review-'], .review"))
          .filter((node) => cleanText(node.textContent).length > 20)
          .length;
      }

      const currentAsin = currentAmazonAsin();
      const candidates = Array.from(document.querySelectorAll("a[href], button, input[type='button'], input[type='submit']"));

      for (const candidate of candidates) {
        const href = absoluteHref(candidate.getAttribute("href") || "");
        const text = cleanText([
          candidate.textContent || "",
          candidate.getAttribute("aria-label") || "",
          candidate.getAttribute("title") || "",
          candidate.getAttribute("class") || "",
          candidate.getAttribute("id") || "",
          href
        ].filter(Boolean).join(" "));

        const haystack = text.toLowerCase();
        const candidateAsin = hrefAsin(href);

        const sameAsinReviewHref = href
          && href.toLowerCase().includes("amazon.")
          && href.toLowerCase().includes("/product-reviews/")
          && (!currentAsin || candidateAsin === currentAsin);

        const loadMoreSignal =
          haystack.includes("cm_cr_arp_d_paging_btm") ||
          haystack.includes("show more reviews") ||
          haystack.includes("more reviews") ||
          haystack.includes("\u591a\u663e\u793a") ||
          haystack.includes("\u663e\u793a\u66f4\u591a");

        if (!sameAsinReviewHref || !loadMoreSignal) continue;

        const beforeCount = visibleReviewCount();
        candidate.scrollIntoView({ block: "center", inline: "nearest" });
        const clickable = candidate.closest("a, button, input") || candidate;
        clickable.click();

        return {
          clicked: true,
          clicked_href: href,
          clicked_text: text.slice(0, 240),
          before_url: location.href,
          before_visible_review_count: beforeCount,
          mode: "dom_click"
        };
      }

      return {
        clicked: false,
        clicked_href: "",
        clicked_text: "",
        before_url: location.href,
        before_visible_review_count: visibleReviewCount(),
        mode: "dom_click"
      };
    }
  });

  return results?.[0]?.result || {
    clicked: false,
    clicked_href: "",
    clicked_text: "",
    before_url: "",
    before_visible_review_count: 0,
    mode: "dom_click"
  };
}

async function collectCurrentProductMoreReviews() {
  setStatus(tPopup("collectingMoreReviews"));

  const activeTab = await getActiveTab();
  const seedProduct = await extractProductFromTab(activeTab);
  const firstUrl = amazonReviewCollectorStartUrl(seedProduct, activeTab.url);

  if (!firstUrl) {
    throw new Error(tPopup("noAmazonAsin"));
  }

  const maxPages = readAutoCollectMaxPages();
  const collected = [];
  const failures = [];
  const pageSnapshots = [];
  const visitedCollectorUrls = new Set();
  const seenReviewPageSignatures = new Set();
  let collectorTab = null;
  let currentUrl = firstUrl;
  let skipNavigationOnce = false;

  try {
    collectorTab = await chrome.tabs.create({ url: currentUrl, active: false });
    if (!collectorTab.id) {
      throw new Error(tPopup("couldNotCreateCollectorTab"));
    }

    for (let pageIndex = 1; pageIndex <= maxPages && currentUrl; pageIndex += 1) {
      if (visitedCollectorUrls.has(currentUrl)) {
        failures.push(tPopup("repeatedCollectorUrl"));
        break;
      }
      visitedCollectorUrls.add(currentUrl);

      if (pageIndex > 1 && !skipNavigationOnce) {
        await chrome.tabs.update(collectorTab.id, { url: currentUrl });
      }
      skipNavigationOnce = false;

      await waitForTabLoad(collectorTab.id);

      const product = await extractProductFromTab({
        id: collectorTab.id,
        url: currentUrl,
        title: `Amazon review page ${pageIndex}`
      });

      const stopReason = backgroundCollectorStopReason(product);
      const nextFromPage = String(product?.metadata?.next_review_page_url || "").trim();
      const currentPageNumber = amazonReviewPageNumberFromUrl(currentUrl);
      const fallbackNextUrl = nextSequentialAmazonReviewUrl(seedProduct, currentUrl, currentPageNumber + 1);
      const nextChoice = chooseNextCollectorUrl(currentUrl, nextFromPage, fallbackNextUrl, visitedCollectorUrls);
      const pageSignature = reviewPageSignatureFromProduct(product);
      const repeatedPageContent = Boolean(pageSignature && seenReviewPageSignatures.has(pageSignature));

      const pageSnapshot = {
        page_index: pageIndex,
        page_number: currentPageNumber,
        url: currentUrl,
        review_count: (product?.reviews || []).length,
        review_visibility_status: product?.metadata?.review_visibility_status || "",
        next_review_page_url: nextFromPage,
        fallback_next_url: fallbackNextUrl,
        selected_next_url: nextChoice.selected_url,
        selected_next_source: nextChoice.source,
        ignored_next_review_page_url: nextChoice.ignored_next_review_page_url,
        load_more_click: null,
        pagination_candidate_count: (product?.metadata?.pagination_candidates || []).length,
        pagination_candidates: (product?.metadata?.pagination_candidates || []).slice(0, 24),
        repeated_page_content: repeatedPageContent,
        stop_reason: repeatedPageContent ? tPopup("repeatedReviewPageContent") : (stopReason || "")
      };

      pageSnapshots.push(pageSnapshot);

      if (stopReason) {
        failures.push(stopReason);
        break;
      }

      if (repeatedPageContent) {
        failures.push(tPopup("repeatedReviewPageContent"));
        break;
      }

      if (pageSignature) {
        seenReviewPageSignatures.add(pageSignature);
      }

      collected.push(product);

      if (shouldClickAmazonLoadMore(nextChoice)) {
        const clickResult = await clickAmazonReviewLoadMoreInTab(collectorTab.id);
        pageSnapshot.load_more_click = clickResult;

        if (clickResult.clicked) {
          await waitForTabLoad(collectorTab.id);
          await delay(1500);

          currentUrl = clickResult.clicked_href || nextChoice.selected_url;
          skipNavigationOnce = true;
          continue;
        }
      }

      currentUrl = nextChoice.selected_url;
    }
  } finally {
    if (collectorTab?.id) {
      try {
        await chrome.tabs.remove(collectorTab.id);
      } catch (error) {
        // Ignore tab cleanup failures during spike collection.
      }
    }
  }

  if (!collected.length) {
    const reason = failures[0] || tPopup("couldNotCollectTabs");
    throw new Error(tPopup("backgroundCollectorStopped").replace("{reason}", reason));
  }

  const { products } = await getSavedProducts();
  const merged = mergeProductsByUrlWithStats(products, collected);
  await setSavedProducts(merged.products);

  $("previewCard").hidden = false;
  $("preview").textContent = JSON.stringify({
    background_review_pages: collected.length,
    collector_pages: pageSnapshots,
    failures,
    merge_stats: merged.stats,
    last_product: normalizeCollectedProductForMerge(collected[collected.length - 1])
  }, null, 2);

  const status = tPopup("backgroundCollectorDone")
    .replace("{pages}", String(collected.length))
    .replace("{added}", String(merged.stats.addedReviews))
    .replace("{duplicates}", String(merged.stats.duplicateReviews))
    .replace("{total}", String(merged.stats.totalReviews));

  const failureSuffix = failures.length
    ? ` ${tPopup("backgroundCollectorStopped").replace("{reason}", failures[0])}`
    : "";
  setStatus(`${status}${failureSuffix}`);
}

async function collectOpenTabs() {
  setStatus(tPopup("collectingOpenTabs"));

  const tabs = await chrome.tabs.query({ currentWindow: true });
  const candidates = tabs.filter((tab) => tab.id && isCollectableTabUrl(tab.url));

  if (!candidates.length) {
    throw new Error(tPopup("noCollectableTabs"));
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
    throw new Error(`${tPopup("couldNotCollectTabs")} ${failures.slice(0, 2).join(" | ")}`);
  }

  const { products } = await getSavedProducts();
  const merged = mergeProductsByUrlWithStats(products, collected);
  await setSavedProducts(merged.products);

  $("previewCard").hidden = false;
  $("preview").textContent = JSON.stringify({
    collected_tabs: collected.length,
    failures,
    merge_stats: merged.stats,
    last_product: normalizeCollectedProductForMerge(collected[collected.length - 1])
  }, null, 2);

  const warningCount = collected.filter((product) => captureDiagnosticMessage(product)).length;
  const failureSuffix = failures.length ? ` ${failures.length} ${tPopup("tabsSkipped")}` : "";
  const warningSuffix = warningCount ? ` ${warningCount} ${tPopup("captureWarnings")}` : "";
  const status = tPopup("collectedTabsMerged")
    .replace("{tabs}", String(collected.length))
    .replace("{added}", String(merged.stats.addedReviews))
    .replace("{duplicates}", String(merged.stats.duplicateReviews))
    .replace("{total}", String(merged.stats.totalReviews));

  setStatus(`${status}${failureSuffix}${warningSuffix}`);
}

async function analyzeWorkspace() {
  const backendUrl = $("backendUrl").value.trim().replace(/\/$/, "") || DEFAULT_BACKEND;
  await chrome.storage.local.set({ backendUrl });

  const { products } = await getSavedProducts();
  if (!products.length) {
    throw new Error(tPopup("saveFirst"));
  }

  setStatus(tPopup("analyzingWorkspace"));

  const response = await fetch(`${backendUrl}/api/v1/analyze-review-workspace`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      workspace_id: `extension_workspace_${Date.now()}`,
      source: "chrome_extension",
      output_language: popupOutputLanguage(),
      products
    })
  });

  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error || tPopup("workspaceFailed"));
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

  setStatus(tPopup("workspaceReady"));
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
  setStatus(tPopup("cleared"));
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
  const stored = await chrome.storage.local.get(["popupLanguage"]);
  popupLanguage = stored.popupLanguage === "zh-CN" ? "zh-CN" : "en";
  applyPopupLanguage();

  bind("extractBtn", saveCurrentProduct);
  bind("collectTabsBtn", collectOpenTabs);
  bind("autoCollectMoreBtn", collectCurrentProductMoreReviews);
  bind("analyzeBtn", analyzeWorkspace);
  bind("copyInsightsBtn", copyInsights);
  bind("copyWorkspaceJsonBtn", copyWorkspaceJson);
  bind("openWorkspaceBtn", openInWebWorkspace);
  bind("clearBtn", clearSavedProducts);
  $("popupLanguageEnglish").addEventListener("click", () => setPopupLanguage("en"));
  $("popupLanguageChinese").addEventListener("click", () => setPopupLanguage("zh-CN"));
  $("backendUrl").addEventListener("change", async () => {
    await chrome.storage.local.set({ backendUrl: $("backendUrl").value.trim() || DEFAULT_BACKEND });
  });
  const maxPagesSelect = $("autoCollectMaxPages");
  if (maxPagesSelect) {
    maxPagesSelect.addEventListener("change", async () => {
      await chrome.storage.local.set({ autoCollectMaxPages: readAutoCollectMaxPages() });
    });
  }
  await updateStats();
});
