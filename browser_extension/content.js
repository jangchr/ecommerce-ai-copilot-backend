(() => {
  function cleanText(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function textFrom(selector) {
    const node = document.querySelector(selector);
    return cleanText(node ? node.textContent : "");
  }

  function attrFrom(selector, attr) {
    const node = document.querySelector(selector);
    return cleanText(node ? node.getAttribute(attr) : "");
  }

  function extractPrice() {
    const selectors = [
      "#corePrice_feature_div .a-offscreen",
      ".a-price .a-offscreen",
      "#priceblock_ourprice",
      "#priceblock_dealprice",
      "[data-a-color='price'] .a-offscreen"
    ];
    for (const selector of selectors) {
      const value = textFrom(selector);
      if (value) return value;
    }
    return "";
  }

  function extractRating() {
    const selectors = [
      "[data-hook='average-star-rating'] .a-icon-alt",
      "#acrPopover .a-icon-alt",
      ".a-icon-star .a-icon-alt"
    ];
    for (const selector of selectors) {
      const value = textFrom(selector);
      if (value) return value;
    }
    return "";
  }

  function extractReviewCount() {
    const selectors = [
      "#acrCustomerReviewText",
      "[data-hook='total-review-count']",
      "#reviewsMedley .a-link-normal"
    ];
    for (const selector of selectors) {
      const value = textFrom(selector);
      if (value) return value;
    }
    return "";
  }

  function extractBullets() {
    return Array.from(document.querySelectorAll("#feature-bullets li, #productFactsDesktopExpander li"))
      .map((node) => cleanText(node.textContent))
      .filter(Boolean)
      .slice(0, 12);
  }

  function extractVisibleReviews() {
    const reviewNodes = Array.from(document.querySelectorAll("[data-hook='review'], .review"));
    const reviews = reviewNodes.map((node) => {
      const rating = cleanText(
        node.querySelector("[data-hook='review-star-rating'] .a-icon-alt, [data-hook='cmps-review-star-rating'] .a-icon-alt, .a-icon-alt")?.textContent
      );
      const title = cleanText(
        node.querySelector("[data-hook='review-title'], .review-title")?.textContent
      );
      const text = cleanText(
        node.querySelector("[data-hook='review-body'], .review-text, .reviewText")?.textContent
      );
      const helpfulText = cleanText(
        node.querySelector("[data-hook='helpful-vote-statement']")?.textContent
      );
      const helpfulMatch = helpfulText.match(/(\d+)\s+people/i);
      return {
        rating,
        title,
        text,
        helpful_count: helpfulMatch ? Number(helpfulMatch[1]) : null,
        source_section: "visible_tab_review"
      };
    }).filter((review) => review.text && review.text.length >= 20);

    return reviews.slice(0, 80);
  }

  function extractCurrentPage() {
    const url = location.href;
    const asinMatch = url.match(/\/(?:dp|gp\/product|product-reviews)\/([A-Z0-9]{10})/i);
    const title = textFrom("#productTitle") || document.title.replace(/Amazon\.com:?/i, "").trim();

    return {
      platform: location.hostname.includes("amazon.") ? "amazon" : "web",
      url,
      asin: asinMatch ? asinMatch[1] : "",
      title,
      brand: textFrom("#bylineInfo"),
      price: extractPrice(),
      rating: extractRating(),
      review_count: extractReviewCount(),
      bullet_points: extractBullets(),
      description: textFrom("#productDescription"),
      reviews: extractVisibleReviews()
    };
  }

  window.CrossGrowthReviewCollector = {
    extractCurrentPage
  };
})();
