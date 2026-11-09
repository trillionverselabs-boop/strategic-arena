from upfront.tools import register_tools


class Ctx:
    def __init__(self):
        self.schemas = {}

    def register_tool(self, name, toolset, schema, handler):
        self.schemas[name] = schema


def test_interventions_and_urls_are_offered_to_the_model():
    c = Ctx()
    register_tools(c)
    props = c.schemas["upfront_run"]["parameters"]["properties"]
    assert "interventions" in props
    assert "urls" in props
    assert "upfront_calibration" in c.schemas
