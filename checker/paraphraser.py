from __future__ import annotations

import re
from random import Random

from checker.suggestions import SYNONYM_HINTS

# Safe phrase-level paraphrase (grammar-preserving)
PHRASE_MAP = {
    "in the contemporary global economy": "within today's global economic landscape",
    "is widely recognized as a key driver of": "is commonly viewed as a major catalyst for",
    "play a central role in cultivating": "are instrumental in developing",
    "the rapid emergence of artificial intelligence (ai) is significantly transforming":
        "the fast-paced rise of Artificial Intelligence (AI) is increasingly reshaping",
    "creating the need for more adaptive and data-driven approaches":
        "which calls for more flexible, evidence-informed approaches",
    "this study empirically examines the impact of":
        "this study empirically investigates the effects of",
    "within the context of university entrepreneurship labs":
        "in university-based entrepreneurship laboratory settings",
    "utilizing a quantitative research design":
        "using a quantitative research design",
    "the results indicate that": "the findings show that",
    "Furthermore, the findings reveal that": "In addition, the results demonstrate that",
    "has become a foundational tool in entrepreneurship education due to its structured approach to visualizing":
        "has become a widely used framework in entrepreneurship education because it offers a structured way to visualize",
    "Despite its widespread adoption": "Although widely adopted",
    "students often encounter challenges": "students frequently face difficulties",
    "The emergence of generative AI provides enhanced support":
        "Generative AI now offers improved support",
    "This development has led to the concept of the":
        "This trend has introduced the idea of an",
    "Although prior research has examined": "While previous studies have explored",
    "limited empirical evidence exists regarding how":
        "there remains limited empirical evidence on how",
    "To address this gap, the present study investigates":
        "To fill this gap, the present study examines",
    "this study pursues three primary objectives":
        "this study addresses three main objectives",
    "This study contributes to the literature in two key ways":
        "This research makes two key contributions to the literature",
    "This study is grounded in Experiential Learning Theory (ELT), which conceptualizes":
        "Drawing on Experiential Learning Theory (ELT), which defines",
    "Innovation capability refers to an individual's ability to transform":
        "Innovation capability describes an individual's capacity to convert",
    "Beyond enhancing individual capabilities, AI-enabled tools may positively influence":
        "In addition to strengthening individual skills, AI-enabled tools can positively affect",
    "Drawing on experiential learning theory, interaction with":
        "Consistent with experiential learning theory, engagement with",
    "This study employs a quantitative, cross-sectional survey design to test":
        "A quantitative cross-sectional survey design was used to test",
    "Data were collected using an online structured questionnaire":
        "An online structured questionnaire was used to collect data",
    "The survey instrument was adapted from validated measurement scales":
        "The questionnaire items were adapted from established measurement scales",
    "The collected data were analyzed using SPSS":
        "SPSS was used to analyze the collected data",
    "To ensure methodological rigor, the study applied established criteria":
        "To ensure rigor, the study followed established criteria",
    "After data screening, a total of 158 valid responses were retained":
        "Following data screening, 158 valid responses were retained",
    "Cronbach's alpha was used to assess internal consistency":
        "Internal consistency was assessed using Cronbach's alpha",
    "Exploratory factor analysis results indicate that":
        "Results of exploratory factor analysis show that",
    "Pearson correlation analysis was conducted to examine":
        "Pearson correlations were computed to assess",
    "Linear regression analysis was conducted to test the hypothesized relationships":
        "Linear regression was performed to test the proposed relationships",
    "The mediating effect of Innovation Capability was examined using":
        "The mediating role of Innovation Capability was tested with",
    "The findings of this study provide empirical evidence for":
        "This study provides empirical evidence for",
    "The results indicate that AI-Driven BMC is significantly and positively associated with":
        "AI-Driven BMC was found to be significantly and positively related to",
    "This study examined the impact of the AI-Driven BMC on":
        "This study investigated how AI-Driven BMC affects",
    "This study advances Experiential Learning Theory by demonstrating how":
        "This research extends Experiential Learning Theory by showing how",
    "The findings offer critical implications for the design of":
        "These findings have important implications for designing",
    "Pedagogical Integration: Educational institutions": "Pedagogical integration: Higher-education institutions",
    "Rather than relying solely on traditional business planning":
        "Instead of depending only on conventional business planning",
    "While this study provides valuable insights, several methodological limitations":
        "Although this study offers useful insights, several methodological limitations",
}

WORD_MAP = {
    **{k: v.split(", ")[0] for k, v in SYNONYM_HINTS.items()},
    "significantly": "substantially",
    "examines": "investigates",
    "examined": "investigated",
    "demonstrates": "shows",
    "indicate": "suggest",
    "indicates": "suggests",
    "utilizing": "using",
    "utilized": "used",
    "facilitates": "supports",
    "facilitate": "support",
    "enhance": "improve",
    "enhances": "improves",
    "enhanced": "improved",
    "Furthermore": "Moreover",
    "However": "Nevertheless",
    "Therefore": "Thus",
    "Additionally": "In addition",
    "particularly": "especially",
    "increasingly": "progressively",
    "conducted": "performed",
    "findings": "results",
    "relationship": "association",
    "relationships": "associations",
    "influence": "effect",
    "influences": "affects",
}

PROTECTED_TERMS = {
    "students",
    "student",
    "analysis",
    "innovation",
    "venture",
    "ai-driven",
    "bmc",
    "business model canvas",
    "innovation capability",
    "venture growth",
    "experiential learning theory",
    "elt",
    "spss",
    "cronbach",
    "pearson",
    "osterwalder",
    "pigneur",
    "kolb",
    "hypothesis",
    "h1",
    "h2",
    "h3",
    "h4",
    "likert",
    "regression",
    "mediation",
    "abstract",
    "index terms",
}

PLACEHOLDER_RE = re.compile(r"(\uE000\d+\uE001)")


def _preserve_case(original: str, replacement: str) -> str:
    if not original:
        return replacement
    if original.isupper():
        return replacement.upper()
    if original[0].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _replace_phrases(text: str) -> str:
    lower = text.lower()
    for phrase, alt in sorted(PHRASE_MAP.items(), key=lambda x: -len(x[0])):
        if phrase in lower:
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            text = pattern.sub(lambda m: _preserve_case(m.group(), alt), text, count=1)
            lower = text.lower()
    return text


def _replace_words(text: str, rng: Random, intensity: float = 0.35) -> str:
    tokens = PLACEHOLDER_RE.split(text)
    out = []
    for token in tokens:
        if PLACEHOLDER_RE.match(token):
            out.append(token)
            continue
        words = re.findall(r"\w+|[^\w\s]+|\s+", token)
        new_words = []
        for w in words:
            if not re.match(r"^\w+$", w):
                new_words.append(w)
                continue
            lw = w.lower()
            if lw in PROTECTED_TERMS:
                new_words.append(w)
            elif lw in WORD_MAP and rng.random() < intensity:
                new_words.append(_preserve_case(w, WORD_MAP[lw]))
            else:
                new_words.append(w)
        out.append("".join(new_words))
    return "".join(out)


def paraphrase_text(text: str, intensity: str = "medium", seed: int | None = None) -> str:
    rng = Random(seed)
    intensity_map = {"light": 0.2, "medium": 0.35, "heavy": 0.5}
    factor = intensity_map.get(intensity, 0.35)

    result = _replace_phrases(text)
    result = _replace_words(result, rng, intensity=factor)
    return result


def paraphrase_for_similarity(
    text: str,
    similarity: float,
    matched_fragment: str = "",
) -> str:
    if similarity >= 35:
        intensity = "medium"
    elif similarity >= 20:
        intensity = "light"
    else:
        return text

    seed = hash(text) & 0xFFFFFFFF
    result = paraphrase_text(text, intensity=intensity, seed=seed)

    if matched_fragment and len(matched_fragment) > 20:
        frag_lower = matched_fragment.lower()
        for phrase, alt in PHRASE_MAP.items():
            if phrase in frag_lower:
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                result = pattern.sub(lambda m: _preserve_case(m.group(), alt), result, count=1)

    return result
