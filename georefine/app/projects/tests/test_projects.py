import unittest
import georefine.app as gr
import georefine.app.keyed_strings.util as ks_util

class ProjectsTest(unittest.TestCase):

    def setUp(self):
        gr.app.config['TESTING'] = True
        self.app = gr.app.test_client()
        self.base_path = '/projects'

    def test_getMap_projects30(self):
        project_id = 30
        path = self.base_path


        json_params = '''
        {"QUERY":{"ID":"outer","FROM":[{"ID":"inner","TABLE":{"ID":"inner","SELECT_GROUP_BY":true,"SELECT":[{"ID":"x_data","EXPRESSION":"func.sum({{result.x}}/{{result.cell.area}})"}],"GROUP_BY":[{"ID":"x_cell_id","EXPRESSION":"{{result.cell.id}}"},{"ID":"x_cell_geom","EXPRESSION":"RawColumn({{result.cell.geom}})"}],"WHERE":[{},["{{result.x}}",">=",0],["{{result.x}}","<=",6254998.2334],["{{result.t}}","==",2008]]}}],"SELECT":[{"ID":"x_geom_id","EXPRESSION":"{{inner.x_cell_id}}"},{"ID":"x_geom","EXPRESSION":"RawColumn({{inner.x_cell_geom}})"},{"ID":"x_data","EXPRESSION":"{{inner.x_data}}"}]},"GEOM_ID_ENTITY":{"ID":"x_geom_id"},"GEOM_ENTITY":{"ID":"x_geom"},"DATA_ENTITY":{"ID":"x_data","max":0.25,"min":0}}
        '''.strip()

        params_key =  ks_util.getKey(json_params)

        wms_params = {
                "TRANSPARENT": "TRUE",
                "SERVICE": "WMS",
                "VERSION": "1.1.1",
                "REQUEST": "GetMap",
                "STYLES": '',
                "FORMAT": "image/png",
                "SRS": "EPSG:4326",
                "BBOX": "-66.2,31,-59.8,37.4",
                "WIDTH": "256",
                "HEIGHT": "256"
                }

        data = {
                #"PARAMS": json_params,
                "PARAMS_KEY": params_key
                }
        data.update(wms_params)
        r = self.app.get("/projects/get_map/%s/" % project_id, query_string=data)
        print r.headers
        print r.data
    
if __name__ == '__main__':
    unittest.main()
