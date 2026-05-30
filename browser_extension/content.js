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
    if (host.includes("amazon.") || search.includes("platform=amazon")) return "amazon";
    if (host.includes("tiktok.") || search.includes("platform=tiktok")) return "tiktok";
    return "web";
  }

  function detectAmazonPageType() {
    const path = location.pathname.toLowerCase();
    const title = cleanText(document.title).toLowerCase();
    const heading = textFrom("h1").toLowerCase();
    const hasSignInInput = Boolean(document.querySelector("#ap_email, input[name='email'], form[name='signIn']"));
    const signInRequired =
      path.includes("/ap/signin") ||
      hasSignInInput ||
      heading.includes("sign in") ||
      title.includes("amazon sign-in");

    if (signInRequired) {
      return {
        page_type: "amazon_sign_in",
        sign_in_required: true
      };
    }

    if (path.includes("/product-reviews/")) {
      return {
        page_type: "amazon_reviews",
        sign_in_required: false
      };
    }

    if (document.querySelector("#productTitle")) {
      return {
        page_type: "amazon_product",
        sign_in_required: false
      };
    }

    return {
      page_type: "amazon_unknown",
      sign_in_required: false
    };
  }

  function amazonReviewVisibilityStatus(pageInfo, reviews) {
    if (pageInfo.sign_in_required) return "sign_in_required";
    if ((reviews || []).length > 0) return "visible_reviews_found";
    if (pageInfo.page_type === "amazon_product") return "no_visible_reviews_on_product_page";
    if (pageInfo.page_type === "amazon_reviews") return "no_visible_reviews_on_reviews_page";
    return "no_visible_reviews";
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

  function firstTextFrom(selectors, root = document) {
    for (const selector of selectors) {
      const value = textFrom(selector, root);
      if (value) return value;
    }
    return "";
  }

  function normalizeReviewTextForDedupe(value) {
    return cleanText(value)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }
  function cleanAmazonReviewText(value) {
    return cleanText(value)
      .replace(/^<img[^>]*>\s*/i, "")
      .replace(/<img[^>]*>/gi, " ")
      .replace(/\bHelpful\b/g, " ")
      .replace(/\bReport\b/g, " ")
      .replace(/\bTranslate review to English\b/gi, " ")
      .replace(/\bThank you for your feedback\b/gi, " ")
      .replace(/\bSorry, there was an error\b/gi, " ")
      .replace(/\bMore\b/g, " ")
      .replace(/\bHide\b/g, " ")
      .replace(/\bClose\b/g, " ")
      .replace(/\bOne person found this(?: helpful)?\b/gi, " ")
      .replace(/\b\d+\s+people\s+found\s+this(?: helpful)?\b/gi, " ")
      .replace(/\s+/g, " ")
      .trim();
  }


  function isAmazonNoiseReviewText(value) {
    const text = cleanAmazonReviewText(value);
    const lower = text.toLowerCase();

    if (!text) return true;
    if (text.length < 18) return true;
    if (lower === "images in this review") return true;
    if (lower === "translate review to english") return true;
    if (lower.includes("there was a problem filtering reviews")) return true;
    if (lower.includes("please reload the page")) return true;
    if (lower.includes("enter mobile number or email")) return true;
    if (lower.includes("sign in") && text.length < 140) return true;

    const imageOnly = lower.includes("images in this review") && text.length < 90;
    if (imageOnly) return true;

    return false;
  }

  function isAmazonAggregateReviewText(value) {
    const text = cleanAmazonReviewText(value);
    const lower = text.toLowerCase();

    const reviewedCount = (lower.match(/reviewed in /g) || []).length;
    const ratingCount = (lower.match(/out of 5 stars/g) || []).length;

    if (text.length > 1200 && reviewedCount >= 3) return true;
    if (text.length > 1200 && ratingCount >= 4) return true;
    if (lower.startsWith("top reviews from") && text.length > 600) return true;
    if (lower.startsWith("top reviews from other countries") && text.length > 600) return true;

    return false;
  }

  function isLikelyTitleOnlyReview(review) {
    const text = cleanAmazonReviewText(review.text);
    const title = cleanText(review.title);

    if (review.rating) return false;
    if (review.helpful_count) return false;
    if (text.length > 55) return false;
    if (title && text !== title) return false;

    const hasSentenceSignal = /[.!?]/.test(text);
    return !hasSentenceSignal;
  }

  function isLowInformationAmazonReview(review) {
    const text = cleanAmazonReviewText(review.text);
    const lower = text.toLowerCase();

    if (!text) return true;
    if (/^amazon customer\s+[1-5](\.0)?\s+out\s+of\s+5\s+stars$/i.test(text)) return true;
    if (/^[1-5](\.0)?\s+out\s+of\s+5\s+stars$/i.test(text)) return true;
    if (/^[1-5](\.0)?\s+stars?$/i.test(text)) return true;

    const hasRating = Boolean(review.rating);
    const hasHelpful = Boolean(review.helpful_count);

    if (!hasRating && !hasHelpful && text.length < 90) return true;

    if (!hasRating && lower.includes("images in this review")) return true;
    if (!hasRating && lower.includes("top reviews from")) return true;

    return false;
  }

  function isContainedDuplicateAmazonReview(review, keptReviews) {
    const normalized = normalizeReviewTextForDedupe(review.text);
    if (!normalized) return true;

    for (const kept of keptReviews) {
      const keptNormalized = normalizeReviewTextForDedupe(kept.text);
      if (!keptNormalized) continue;

      if (normalized === keptNormalized) return true;

      const currentIsWeaker = !review.rating && !review.helpful_count;
      if (currentIsWeaker && keptNormalized.includes(normalized) && normalized.length >= 24) {
        return true;
      }

      const currentLooksAggregate = !review.rating && normalized.includes(keptNormalized) && keptNormalized.length >= 48;
      if (currentLooksAggregate) {
        return true;
      }
    }

    return false;
  }

  function extractAmazonReviewTitle(node) {
    const raw = firstTextFrom([
      "[data-hook='review-title'] span:not(.a-icon-alt)",
      "[data-hook='review-title']",
      ".review-title span:not(.a-icon-alt)",
      ".review-title",
      "a[data-hook='review-title'] span",
      "a.review-title span"
    ], node);

    return cleanText(raw.replace(/^[0-5](\.[0-9])?\s+out\s+of\s+5\s+stars/i, ""));
  }

  function extractAmazonReviewBody(node) {
    const body = firstTextFrom([
      "[data-hook='review-body'] span",
      "[data-hook='review-body']",
      ".review-text-content span",
      ".review-text-content",
      ".review-text span",
      ".review-text",
      "[data-hook='review-collapsed'] span",
      "[data-hook='review-collapsed']",
      ".a-expander-content.reviewText",
      ".a-expander-content"
    ], node);

    if (body) return cleanAmazonReviewText(body);

    return cleanAmazonReviewText(node.innerText || node.textContent || "");
  }

  function extractAmazonReviewRating(node) {
    return firstTextFrom([
      "[data-hook='review-star-rating'] .a-icon-alt",
      "[data-hook='cmps-review-star-rating'] .a-icon-alt",
      ".review-rating .a-icon-alt",
      ".a-icon-alt"
    ], node);
  }

  function extractAmazonHelpfulCount(node) {
    const helpfulText = firstTextFrom([
      "[data-hook='helpful-vote-statement']",
      ".cr-vote-text",
      ".review-votes",
      "[class*='helpful']"
    ], node);

    return helpfulCountFromText(helpfulText);
  }

  function amazonReviewCandidateNodes() {
    const selectors = [
      "[data-hook='review']",
      "[id^='customer_review-']",
      "#cm-cr-dp-review-list [class*='review']",
      "#reviewsMedley [class*='review']",
      "#customerReviews [class*='review']",
      ".reviews-content [class*='review']"
    ];

    const nodes = [];
    for (const selector of selectors) {
      nodes.push(...Array.from(document.querySelectorAll(selector)));
    }

    const unique = [];
    const seen = new Set();
    for (const node of nodes) {
      if (!node || seen.has(node)) continue;
      seen.add(node);
      unique.push(node);
    }

    return unique;
  }

  function ratingBucketFromText(value) {
    const match = String(value || "").match(/([1-5])(?:\.0)?\s+out\s+of\s+5/i);
    if (!match) return "unknown";
    return `${match[1]}_star`;
  }

  function amazonRatingDistribution(reviews) {
    const distribution = {
      "5_star": 0,
      "4_star": 0,
      "3_star": 0,
      "2_star": 0,
      "1_star": 0,
      "unknown": 0
    };

    for (const review of reviews || []) {
      const bucket = ratingBucketFromText(review.rating);
      distribution[bucket] = (distribution[bucket] || 0) + 1;
    }

    return distribution;
  }

  function amazonVisibleSampleWarning(pageInfo, reviews) {
    if (pageInfo.sign_in_required) {
      return "Amazon sign-in required. The extension only collects visible page content.";
    }

    if ((reviews || []).length > 0) {
      return "Visible Amazon review sample only. Sorting may reflect Amazon's current page state, not the full review set.";
    }

    return "No visible Amazon reviews found on the current page.";
  }

  function extractAmazonVisibleReviews() {
    const reviewNodes = amazonReviewCandidateNodes();
    const keptReviews = [];
    const skippedCounts = {};
    const skippedSamples = [];

    function recordSkippedReview(reason, review, index) {
      skippedCounts[reason] = (skippedCounts[reason] || 0) + 1;

      if (skippedSamples.length >= 16) return;

      const cleanedText = cleanAmazonReviewText(review?.text || "");
      skippedSamples.push({
        index,
        reason,
        rating: review?.rating || "",
        title: cleanText(review?.title || "").slice(0, 140),
        text_length: cleanedText.length,
        text_preview: cleanedText.slice(0, 220),
        helpful_count: review?.helpful_count ?? null
      });
    }

    for (const [index, node] of reviewNodes.entries()) {
      const review = {
        rating: extractAmazonReviewRating(node),
        title: extractAmazonReviewTitle(node),
        text: extractAmazonReviewBody(node),
        helpful_count: extractAmazonHelpfulCount(node),
        source_section: "amazon_visible_review"
      };

      if (isAmazonNoiseReviewText(review.text)) {
        recordSkippedReview("noise_text", review, index);
        continue;
      }

      if (isAmazonAggregateReviewText(review.text)) {
        recordSkippedReview("aggregate_text", review, index);
        continue;
      }

      if (isLikelyTitleOnlyReview(review)) {
        recordSkippedReview("title_only", review, index);
        continue;
      }

      if (isLowInformationAmazonReview(review)) {
        recordSkippedReview("low_information", review, index);
        continue;
      }

      if (isContainedDuplicateAmazonReview(review, keptReviews)) {
        recordSkippedReview("contained_duplicate", review, index);
        continue;
      }

      keptReviews.push(review);
    }

    return {
      reviews: keptReviews.slice(0, 80),
      raw_candidate_count: reviewNodes.length,
      extraction_debug: {
        candidate_count: reviewNodes.length,
        kept_count: keptReviews.length,
        returned_count: Math.min(keptReviews.length, 80),
        skipped_counts: skippedCounts,
        skipped_samples: skippedSamples,
        truncated_to_limit: keptReviews.length > 80
      }
    };
  }

  function absoluteAmazonHref(href) {
    try {
      return new URL(href, location.href).href;
    } catch (error) {
      return "";
    }
  }

  function amazonPaginationNodeText(node) {
    return cleanText([
      node.textContent || "",
      node.getAttribute("aria-label") || "",
      node.getAttribute("title") || "",
      node.getAttribute("class") || "",
      node.getAttribute("id") || "",
      node.getAttribute("rel") || ""
    ].filter(Boolean).join(" "));
  }

  function extractAmazonPaginationCandidates() {
    const anchors = Array.from(document.querySelectorAll("a[href]"));
    const candidates = [];
    const seen = new Set();

    for (const anchor of anchors) {
      const href = absoluteAmazonHref(anchor.getAttribute("href"));
      if (!href) continue;

      const text = amazonPaginationNodeText(anchor);
      const ariaLabel = cleanText(anchor.getAttribute("aria-label") || "");
      const title = cleanText(anchor.getAttribute("title") || "");
      const className = cleanText(anchor.getAttribute("class") || "");
      const id = cleanText(anchor.getAttribute("id") || "");
      const rel = cleanText(anchor.getAttribute("rel") || "");
      const paginationParent = anchor.closest("li.a-last, .a-last, .a-pagination li");
      const parentClassName = cleanText(paginationParent?.getAttribute("class") || "");
      const haystack = `${href} ${text} ${ariaLabel} ${title} ${className} ${id} ${rel} ${parentClassName}`.toLowerCase();

      const looksLikePagination =
        haystack.includes("product-reviews") ||
        haystack.includes("pagenumber=") ||
        haystack.includes("nextpagetoken") ||
        haystack.includes("cm_cr_getr") ||
        haystack.includes("a-last") ||
        haystack.includes("next") ||
        /[\u6b21\u4e0b]\s*[\u3078\u306e\u4e00]?/.test(haystack);

      if (!looksLikePagination) continue;

      const key = `${href}|${text}|${ariaLabel}`;
      if (seen.has(key)) continue;
      seen.add(key);

      candidates.push({
        text,
        href,
        aria_label: ariaLabel,
        title,
        class_name: className,
        parent_class_name: parentClassName,
        id,
        rel
      });
    }

    return candidates.slice(0, 30);
  }
  function amazonCurrentReviewAsin() {
    const match = location.href.match(/\/(?:dp|gp\/product|product-reviews)\/([A-Z0-9]{10})/i);
    return match ? match[1].toUpperCase() : "";
  }

  function amazonCandidateReviewAsin(value) {
    const match = String(value || "").match(/\/(?:dp|gp\/product|product-reviews)\/([A-Z0-9]{10})/i);
    return match ? match[1].toUpperCase() : "";
  }

  function isAmazonSafeReviewPaginationCandidate(candidate) {
    if (!candidate?.href) return false;

    let url;
    try {
      url = new URL(candidate.href);
    } catch (error) {
      return false;
    }

    const hostname = url.hostname.toLowerCase();
    const pathname = url.pathname.toLowerCase();
    if (!hostname.includes("amazon.")) return false;
    if (!pathname.includes("/product-reviews/")) return false;

    const currentAsin = amazonCurrentReviewAsin();
    const candidateAsin = amazonCandidateReviewAsin(candidate.href);
    if (currentAsin && candidateAsin !== currentAsin) return false;

    const haystack = [
      candidate.href || "",
      candidate.text || "",
      candidate.aria_label || "",
      candidate.title || "",
      candidate.class_name || "",
      candidate.parent_class_name || "",
      candidate.id || "",
      candidate.rel || ""
    ].join(" ").toLowerCase();

    if (url.hash && ["#skippedlink", "#customerreviews", "#reviews-filter-bar"].includes(url.hash.toLowerCase())) {
      return false;
    }

    if (url.searchParams.has("filterByStar")) return false;
    if (url.searchParams.get("formatType") === "current_format") return false;
    if (url.searchParams.get("reviewerType") === "avp_only_reviews") return false;

    if (haystack.includes("histogram-row-container")) return false;
    if (haystack.includes("nav-")) return false;
    if (haystack.includes("buyagain")) return false;
    if (haystack.includes("audible")) return false;
    if (haystack.includes("customer-preferences")) return false;
    if (haystack.includes("verified purchase")) return false;
    if (haystack.includes("\u5df2\u786e\u8ba4\u8d2d\u4e70")) return false;

    return true;
  }

  function amazonCandidateNextSignal(candidate) {
    const haystack = [
      candidate.text || "",
      candidate.aria_label || "",
      candidate.title || "",
      candidate.class_name || "",
      candidate.parent_class_name || "",
      candidate.id || "",
      candidate.rel || ""
    ].join(" ").toLowerCase();

    return (
      candidate.rel === "next" ||
      haystack.includes("a-last") ||
      /\bnext\b/.test(haystack) ||
      haystack.includes("next page") ||
      haystack.includes("\u6b21\u3078") ||
      haystack.includes("\u6b21\u306e\u30da\u30fc\u30b8") ||
      haystack.includes("\u4e0b\u4e00\u9875") ||
      haystack.includes("\u663e\u793a\u66f4\u591a") ||
      haystack.includes("\u591a\u663e\u793a")
    );
  }

  function amazonCandidateLoadMoreSignal(candidate) {
    const haystack = [
      candidate.href || "",
      candidate.text || "",
      candidate.aria_label || "",
      candidate.title || "",
      candidate.class_name || "",
      candidate.parent_class_name || "",
      candidate.id || "",
      candidate.rel || ""
    ].join(" ").toLowerCase();

    return (
      haystack.includes("cm_cr_arp_d_paging_btm") ||
      haystack.includes("show more reviews") ||
      haystack.includes("more reviews") ||
      haystack.includes("\u591a\u663e\u793a") ||
      haystack.includes("\u663e\u793a\u66f4\u591a")
    );
  }
  function extractAmazonNextReviewPageUrl() {
    const candidates = extractAmazonPaginationCandidates();
    const safeCandidates = candidates.filter(isAmazonSafeReviewPaginationCandidate);

    let currentPage = 1;
    try {
      currentPage = Number(new URL(location.href).searchParams.get("pageNumber") || "1") || 1;
    } catch (error) {
      currentPage = 1;
    }

    const explicitNext = safeCandidates.find((candidate) => {
      if (!amazonCandidateNextSignal(candidate) && !amazonCandidateLoadMoreSignal(candidate)) return false;

      try {
        const url = new URL(candidate.href);
        const pageNumber = Number(url.searchParams.get("pageNumber") || "0") || 0;
        const hasForwardPageNumber = pageNumber > currentPage;
        const hasNextToken = url.searchParams.has("nextPageToken");
        const hasLoadMoreRef = amazonCandidateLoadMoreSignal(candidate);
        return hasForwardPageNumber || hasNextToken || hasLoadMoreRef;
      } catch (error) {
        return false;
      }
    });

    if (explicitNext?.href) {
      return explicitNext.href;
    }

    const numberedCandidates = [];
    for (const candidate of safeCandidates) {
      try {
        const url = new URL(candidate.href);
        const pageNumber = Number(url.searchParams.get("pageNumber") || "0") || 0;
        if (pageNumber > currentPage) {
          numberedCandidates.push({ pageNumber, href: url.href });
        }
      } catch (error) {
        continue;
      }
    }

    numberedCandidates.sort((left, right) => left.pageNumber - right.pageNumber);
    return numberedCandidates[0]?.href || "";
  }


  function extractAmazonPage() {
    const url = location.href;
    const pageInfo = detectAmazonPageType();
    const asinMatch = url.match(/\/(?:dp|gp\/product|product-reviews)\/([A-Z0-9]{10})/i);
    const reviewPayload = pageInfo.sign_in_required ? { reviews: [], raw_candidate_count: 0 } : extractAmazonVisibleReviews();
    const reviews = reviewPayload.reviews || [];

    const title =
      textFrom("#productTitle") ||
      metaContent("og:title") ||
      (pageInfo.sign_in_required ? "Amazon sign-in required" : document.title.replace(/Amazon\.com:?/i, "").trim());

    return {
      platform: "amazon",
      url,
      asin: asinMatch ? asinMatch[1] : "",
      title,
      brand: textFrom("#bylineInfo"),
      price: pageInfo.sign_in_required ? "" : extractPrice(),
      rating: pageInfo.sign_in_required ? "" : extractAmazonRating(),
      review_count: pageInfo.sign_in_required ? "" : extractAmazonReviewCount(),
      bullet_points: pageInfo.sign_in_required ? [] : extractAmazonBullets(),
      description: pageInfo.sign_in_required ? "" : textFrom("#productDescription"),
      reviews,
      metadata: {
        extractor: "amazon_visible_dom",
        page_type: pageInfo.page_type,
        sign_in_required: pageInfo.sign_in_required,
        review_visibility_status: amazonReviewVisibilityStatus(pageInfo, reviews),
        source_scope: "visible_page_sample",
        sample_warning: amazonVisibleSampleWarning(pageInfo, reviews),
        rating_distribution: amazonRatingDistribution(reviews),
        raw_review_candidate_count: reviewPayload.raw_candidate_count || 0,
        visible_review_count: reviews.length,
        review_extraction_debug: reviewPayload.extraction_debug || null,
        next_review_page_url: pageInfo.sign_in_required ? "" : extractAmazonNextReviewPageUrl(),
        pagination_candidates: pageInfo.sign_in_required ? [] : extractAmazonPaginationCandidates()
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
    detectAmazonPageType,
    extractAmazonPage,
    extractTikTokPage,
    extractGenericPage,
    extractCurrentPage
  };
})();
