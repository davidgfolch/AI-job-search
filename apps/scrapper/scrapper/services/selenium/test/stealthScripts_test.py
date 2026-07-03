class TestStealthScripts:

    def test_stealth_scripts_js_is_string(self):
        from scrapper.services.selenium import stealthScripts
        assert isinstance(stealthScripts.STEALTH_SCRIPTS_JS, str)

    def test_stealth_scripts_js_contains_stealth_code(self):
        from scrapper.services.selenium import stealthScripts
        assert 'navigator' in stealthScripts.STEALTH_SCRIPTS_JS
        assert 'webdriver' in stealthScripts.STEALTH_SCRIPTS_JS
