import unittest


class TestFLask(unittest.TestCase):

    def test_to_text_with_dtime(self):
        from werkzeug.test import Client
        from emec_2021.flaskapp import app

        c = Client(app)
        for format_ in ['text', 'xml']:
            response = c.get(f"/?minmag=6&start=2009-01-01&format={format_}")
            assert response.status_code == 200
            data = response.data

    def test_to_text(self):
        from werkzeug.test import Client
        from emec_2021.flaskapp import app
        c = Client(app)
        response = c.get("/?mag>8=7&format=text")
        assert response.status_code == 400

        c = Client(app)
        data = c.get("/?minmag=8").data
        for format_ in ['text', 'xml']:
            response = c.get(f"/?minmag=8&format={format_}")
            assert response.status_code == 200
            if format_ == 'xml':
                assert response.data == data

        # FIXME: test POST!


if __name__ == '__main__':
    unittest.main()
