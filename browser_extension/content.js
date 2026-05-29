(() => {
  function cleanText(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function textFrom(selector, root = document) {
    const node = root.querySelector(selector);
    return cleanText(node ? node.textContent : "");
  }

  function attrFrom(selector, attr, root = document) {
    const node = root.querySelector(selector);
    return cleanText(node ? node.getAttribute(attr) : "");
  }

  function metaContent(name) {
    return (
      attrFrom(`meta[property="${name}"]`, "content") ||
      attrFrom(`meta[name="${name}"]`, "content")
    );
  }

  function uniqueByText(items) {
    const seen = new Set();
    const output = [];
    for (const item of items) {
      const key = cleanText(item.text).toLowerCase();
      if (!key || seen.has(key)) continue;
      seen.add(key);
      output.push(item);
    }
    return output;
  }

  function helpfulCountFromText(value) {
    const text = cleanText(value);
    const numeric = text.match(/(\d+)\s+(?:people|person|likes?|like)/i);
    if (numeric) return Number(numeric[1]);
    if (/one\s+person/i.test(text)) return 1;
    return null;
  }

  function detectPlatform() {
    const host = location.hostname.toLowerCase();
    const search = location.search.toLowerCase();
    if (host.includes("amazon.")) return "amazon";
    if (host.includes("tiktok.") || search.includes("platform=tiktok")) return "tiktok";
    return "web";
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

  function extractAmazonRating() {
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

  function extractAmazonReviewCount() {
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

  function extractAmazonBullets() {
    return Array.from(document.querySelectorAll("#feature-bullets li, #productFactsDesktopExpander li"))
      .map((node) => cleanText(node.textContent))
      .filter(Boolean)
      .slice(0, 12);
  }

  function extractAmazonVisibleReviews() {
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
      return {
        rating,
        title,
        text,
        helpful_count: helpfulCountFromText(helpfulText),
        source_section: "amazon_visible_review"
      };
    }).filter((review) => review.text && review.text.length >= 20);

    return uniqueByText(reviews).slice(0, 80);
  }

  function extractAmazonPage() {
    const url = location.href;
    const asinMatch = url.match(/\/(?:dp|gp\/product|product-reviews)\/([A-Z0-9]{10})/i);
    const title = textFrom("#productTitle") || metaContent("og:title") || document.title.replace(/Amazon\.com:?/i, "").trim();

    return {
      platform: "amazon",
      url,
      asin: asinMatch ? asinMatch[1] : "",
      title,
      brand: textFrom("#bylineInfo"),
      price: extractPrice(),
      rating: extractAmazonRating(),
      review_count: extractAmazonReviewCount(),
      bullet_points: extractAmazonBullets(),
      description: textFrom("#productDescription"),
      reviews: extractAmazonVisibleReviews(),
      metadata: {
        extractor: "amazon_visible_dom"
      }
    };
  }

  function extractTikTokCreator() {
    const selectors = [
      "[data-e2e='browse-username']",
      "[data-e2e='video-author-uniqueid']",
      "a[href^='/@']",
      "a[href*='tiktok.com/@']",
      "[data-testid='creator']"
    ];
    for (const selector of selectors) {
      const value = textFrom(selector);
      if (value) return value;
    }
    const pathMatch = location.pathname.match(/@([^/]+)/);
    return pathMatch ? `@${pathMatch[1]}` : "";
  }

  function extractTikTokCaption() {
    const selectors = [
      "[data-e2e='browse-video-desc']",
      "[data-e2e='video-desc']",
      "[data-testid='caption']",
      "h1",
      "main h2"
    ];
    for (const selector of selectors) {
      const value = textFrom(selector);
      if (value) return value;
    }
    return metaContent("og:description") || metaContent("description") || document.title;
  }

  function extractTikTokHashtags() {
    const tags = Array.from(document.querySelectorAll("a[href*='/tag/'], a[href*='hashtag'], [data-testid='hashtag']"))
      .map((node) => cleanText(node.textContent))
      .filter((text) => text.startsWith("#") || text.length > 1)
      .slice(0, 20);
    return Array.from(new Set(tags));
  }

  function extractTikTokVisibleComments() {
    const selectors = [
      "[data-e2e='comment-item']",
      "[data-e2e='comment-level-1']",
      "[data-testid='comment-item']",
      "[class*='DivCommentItemContainer']",
      "[class*='CommentItemContainer']",
      "[class*='comment-item']"
    ];

    const nodes = [];
    for (const selector of selectors) {
      nodes.push(...Array.from(document.querySelectorAll(selector)));
    }

    const reviews = nodes.map((node) => {
      const commentText =
        textFrom("[data-e2e='comment-level-1'] p", node) ||
        textFrom("[data-testid='comment-text']", node) ||
        textFrom("p", node) ||
        cleanText(node.textContent);

      const likeText =
        textFrom("[data-e2e='comment-like-count']", node) ||
        textFrom("[data-testid='comment-like-count']", node) ||
        textFrom("[class*='like']", node);

      return {
        rating: null,
        title: "",
        text: commentText,
        helpful_count: helpfulCountFromText(likeText),
        source_section: "tiktok_visible_comment"
      };
    }).filter((review) => review.text && review.text.length >= 8);

    return uniqueByText(reviews).slice(0, 100);
  }

  function extractTikTokPage() {
    const caption = extractTikTokCaption();
    const creator = extractTikTokCreator();
    const hashtags = extractTikTokHashtags();

    return {
      platform: "tiktok",
      url: location.href,
      asin: "",
      title: caption || document.title,
      brand: creator,
      price: "",
      rating: null,
      review_count: "",
      bullet_points: hashtags,
      description: caption,
      reviews: extractTikTokVisibleComments(),
      metadata: {
        extractor: "tiktok_visible_dom",
        creator,
        hashtags,
        og_title: metaContent("og:title"),
        og_description: metaContent("og:description")
      }
    };
  }

  function extractGenericVisibleComments() {
    const nodes = Array.from(document.querySelectorAll(
      "article, blockquote, [class*='review'], [class*='comment'], [id*='review'], [id*='comment'], p"
    ));

    const reviews = nodes.map((node) => ({
      rating: null,
      title: "",
      text: cleanText(node.textContent),
      helpful_count: null,
      source_section: "generic_visible_text"
    })).filter((review) => {
      const text = review.text.toLowerCase();
      if (review.text.length < 30) return false;
      if (text.includes("cookie") && text.includes("privacy")) return false;
      if (text.includes("sign in") && text.length < 80) return false;
      return true;
    });

    return uniqueByText(reviews).slice(0, 80);
  }

  function extractGenericPage() {
    const title = textFrom("h1") || metaContent("og:title") || document.title;

    return {
      platform: "web",
      url: location.href,
      asin: "",
      title,
      brand: "",
      price: "",
      rating: null,
      review_count: "",
      bullet_points: [],
      description: metaContent("og:description") || metaContent("description"),
      reviews: extractGenericVisibleComments(),
      metadata: {
        extractor: "generic_visible_dom",
        hostname: location.hostname
      }
    };
  }

  function extractCurrentPage() {
    const platform = detectPlatform();
    if (platform === "amazon") return extractAmazonPage();
    if (platform === "tiktok") return extractTikTokPage();
    return extractGenericPage();
  }

  window.CrossGrowthReviewCollector = {
    detectPlatform,
    extractAmazonPage,
    extractTikTokPage,
    extractGenericPage,
    extractCurrentPage
  };
})();
