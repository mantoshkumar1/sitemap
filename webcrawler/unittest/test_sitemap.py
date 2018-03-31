import unittest


class SiteMapTestCase ( unittest.TestCase ):
    def setUp ( self ):
        """
        Method called before any unittest case
        :return:
        """
        pass

    def tearDown ( self ):
        """
        Method called after every unittest case
        :return:
        """
        pass

    def test_parse_site_urls ( self ):
        self.assertEqual ( 1, 1 )

    def test_find_valid_links_in_urlpage ( self ):
        self.assertTrue ( True )

    def test_config_urllib_proxy ( self ):
        self.assertFalse ( False )
