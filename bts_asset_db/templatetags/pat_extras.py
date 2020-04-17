from django import template
register = template.Library()

results = {
    240: ("", "", ""),
    241: ("", "", ""),
    242: ("Current: ", "Passed: ", "Resistance (Ohms): "),
    243: ("Passed: ", "Resistance (MOhms): ", ""),
    244: ("Passed: ", "Current (mAmp): ", ""),
    245: ("Passed: ", "Current (mAmp): ", ""),
    246: ("Passed: ", "Load: ", "Leakage: "),
    247: ("Passed: ", "Current (mAmp): ", ""),
    248: ("Passed: ", "Resistance: ", ""),
    249: ("", "", ""),
    250: ("", "", ""),
}

test_nos = {
    240: "Overall Pass",
    241: "Overall Fail",
    242: "Earth Resistance",
    243: "Earth Insulation",
    244: "Substitute Leakage",
    245: "Flash Leakage",
    246: "Load/Leakage",
    247: "Flash Leakage",
    248: "Continuity",
    249: "Polarity Pass",
    250: "Unknown/Other",
}


@register.filter
def index(indexable, i):
    return indexable[i]


@register.filter
def testtranslate(test_no):
    return test_nos[test_no]


@register.filter
def preftranslate(param, test_no):
    return results[test_no]