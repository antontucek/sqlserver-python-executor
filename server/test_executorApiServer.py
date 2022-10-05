import json
import unittest
import time

from executorApiServer import api, executor_get_python_cmd, SCRIPT_DIR, TOKEN


class TestApi(unittest.TestCase):

    def setUp(self):
        self.ctx = api.app_context()
        self.ctx.push()
        self.client = api.test_client()

    def tearDown(self):
        self.ctx.pop()

    def test_executor_get_python_cmd(self):
        sn: str = 'testScript.py'
        r = executor_get_python_cmd(script_name=sn)
        self.assertEqual(f"python3 {SCRIPT_DIR}/{sn}", r)
        r = executor_get_python_cmd(script_name=sn, parameters="--ignore")
        self.assertEqual(f"python3 {SCRIPT_DIR}/{sn} --ignore", r)

    def test_executor_python(self):
        path: str = "/executor/python/"
        hed = {
            'Authorization': 'EMPTY'
        }
        req = {
            "script_name": "testScript.py"
        }
        response = self.client.post(path, headers=hed, data=None)
        self.assertEqual(401, response.status_code, 'Wrong token')

        hed['Authorization'] = 'Bearer ' + TOKEN
        response = self.client.post(path, headers=hed, data=None)
        self.assertEqual(400, response.status_code, 'Empty body test')

        req['parameters'] = '-r=1'
        response = self.client.post(path, headers=hed, data=json.dumps(req), content_type='application/json')
        self.assertEqual(500, response.status_code, 'Exit code 1')
        del req['parameters']

        req['parameters'] = '-s=1'
        start_time = time.time()
        response = self.client.post(path, headers=hed, data=json.dumps(req), content_type='application/json')
        duration_sec = (time.time() - start_time)
        self.assertEqual(200, response.status_code, 'Correct request')
        self.assertIn('ok', response.get_json(), 'Correct request')
        self.assertTrue('Finished' in response.get_json()['ok'], 'Correct request')
        self.assertGreaterEqual(duration_sec, 1.00, "Request must take more than 1 second")
        self.assertLessEqual(duration_sec, 2.00, "Request must take less than 2 seconds")
        del req['parameters']

        req['parameters'] = '-s=1'
        req['wait_flag'] = False
        start_time = time.time()
        response = self.client.post(path, headers=hed, data=json.dumps(req), content_type='application/json')
        duration_sec = (time.time() - start_time)
        self.assertIn('ok', response.get_json(), 'Correct request')
        self.assertTrue('queue' in response.get_json()['ok'], 'Correct request')
        self.assertLessEqual(duration_sec, 0.50, "Request must be finished in less than 0.5 seconds")
        del req['parameters']
        del req['wait_flag']

        req['script_name'] = '__notexists.py'
        response = self.client.post(path, headers=hed, data=json.dumps(req), content_type='application/json')
        self.assertEqual(500, response.status_code, 'Not existing script')
        self.assertTrue('not found' in response.get_json()['error'], 'Not existing script')


if __name__ == '__main__':
    unittest.main(verbosity=2)

