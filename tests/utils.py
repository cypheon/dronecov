import xml.etree.ElementTree as ET

def validate_svg(response, coverage):
    xml = ET.fromstring(response.text)
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    cov = xml.find('./svg:g[2]/svg:text[3]', ns).text
    actual = cov
    expected = coverage + '\u2009%'
    if actual != expected:
        raise AssertionError(actual + " != " + expected)
