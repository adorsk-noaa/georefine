import unittest
from georefine.util.sa.tests.basetest import BaseTest
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects
from georefine.app.projects.util import services
from georefine.app import db
import os

_basedir = os.path.abspath(os.path.dirname(__file__))

class Services_Test(BaseTest):

    def setUp(self):
        super(Services_Test, self).setUp()
        db.session.bind = self.connection
        self.schema = self.setUpSchemaAndData1()
        #manage_projects.setUpSchema(self.project)      
        #manage_projects.setUpData(self.project)

    def testGetKeyedResults(self):
        return #INACTIVE
        project = Project(id=1, name='test')
        project.schema = self.schema

        bucket_entity1 = {'ID': 'bucket', 'EXPRESSION': '{{test1.id}}', 'AS_HISTOGRAM': True, 'ALL_VALUES': True, 'MIN': 0, 'MAX': 5, 'NUM_BUCKETS': 5}
        #bucket_entity2 = {'ID': 'bucket', 'EXPRESSION': '{{test1.id}}', 'AS_HISTOGRAM': True, 'NUM_BUCKETS': 10, 'CONTEXT': {
            #"WHERE": [["{{test1.id}}", "in", [2,3]]]
            #}}

        key = {
                #"KEY_ENTITY" : {'EXPRESSION': '{{test1.id}}', 'ALL_VALUES': True},
                #"LABEL_ENTITY" : {'EXPRESSION': '{{test1.name}}'}
                "KEY_ENTITY" : bucket_entity1
                }

        primary_q = {
                "AS_DICTS": True, 
                "ID": "primary_q",
                "SELECT" : [
                    {'ID': "t1id", 'EXPRESSION': '{{test1.id}}'},
                    ],
                "GROUP_BY": [
                    {"ID": "t1id"},
                    bucket_entity1
                    ],
                "SELECT_GROUP_BY": True,
                }

        results = services.get_keyed_results(project, key, [primary_q])
        print results

    def testProject30KeyedResults(self):
        return #INACTIVE
        project = db.session.query(Project).filter(Project.id == 30).one()
        project.schema = manage_projects.getProjectSchema(project)

        import simplejson as json
        json_params = '''
        {
   "KEY":{
      "KEY_ENTITY":{
         "ID":"substrate_id",
         "EXPRESSION":"{{result.substrate.id}}"
      },
      "LABEL_ENTITY":{
         "ID":"substrate_name",
         "EXPRESSION":"{{result.substrate.name}}"
      }
   },
   "QUERIES":[
      {
         "SELECT":[
            {
               "ID":"count_cell_id",
               "EXPRESSION":"func.count({{inner.cell_id}})"
            }
         ],
         "FROM":[
            {
               "ID": "inner",
               "TABLE":{
                  "SELECT":[
                     {
                        "ID":"cell_id",
                        "EXPRESSION":"{{result.cell.id}}"
                     }
                  ],
                  "FROM":[],
                  "GROUP_BY":[
                     {"ID":"cell_id"},
                     {"ID":"substrate_id","EXPRESSION":"{{result.substrate.id}}" }, 
                     {"ID":"substrate_name","EXPRESSION":"{{result.substrate.name}}"}
                  ],
                  "WHERE":[
                    ["{{result.t}}", "==", "2009"]
                  ],
                  "ORDER_BY":[

                  ],
                  "ID":"inner",
                  "SELECT_GROUP_BY":true
               }
            }
         ],
         "GROUP_BY":[
                     {"ID":"substrate_id","EXPRESSION":"{{inner.substrate_id}}" }, 
                     {"ID":"substrate_name","EXPRESSION":"{{inner.substrate_name}}"}
         ],
         "WHERE":[],
         "ORDER_BY":[],
         "ID":"outer",
         "SELECT_GROUP_BY":true
      }
   ]
}
        '''


        params = json.loads(json_params)
        results = services.get_keyed_results(project, params['KEY'], params['QUERIES'])
        print results



    def testProjects30Histogram(self):
        project = db.session.query(Project).filter(Project.id == 30).one()
        project.schema = manage_projects.getProjectSchema(project)

        requests_json = '''
        [{"ID":"keyed_results","REQUEST":"execute_keyed_queries","PARAMETERS":{"KEY":{"KEY_ENTITY":{"ID":"x","EXPRESSION":"{{result.x}}","ALL_VALUES":true,"AS_HISTOGRAM":true,"CONTEXT":{"WHERE":[["{{result.t}}","==",2008]]}}},"QUERIES":[{"ID":"base","SELECT":[{"ID":"count_cell_id","EXPRESSION":"func.count({{inner.cell_id}})"}],"FROM":[{"ID":"inner","TABLE":{"ID":"inner","SELECT_GROUP_BY":true,"SELECT":[{"ID":"cell_id","EXPRESSION":"{{result.cell.id}}"}],"FROM":[],"WHERE":[["{{result.t}}","==",2008]],"GROUP_BY":[{"ID":"cell_id"},{"ID":"x","EXPRESSION":"{{result.x}}","ALL_VALUES":true,"AS_HISTOGRAM":true,"CONTEXT":{"WHERE":[["{{result.t}}","==",2008]]}}],"ORDER_BY":[]}}],"WHERE":[],"GROUP_BY":[{"ID":"x","EXPRESSION":"{{inner.x}}"}],"ORDER_BY":[],"SELECT_GROUP_BY":true},{"ID":"primary","SELECT":[{"ID":"count_cell_id","EXPRESSION":"func.count({{inner.cell_id}})"}],"FROM":[{"ID":"inner","TABLE":{"ID":"inner","SELECT_GROUP_BY":true,"SELECT":[{"ID":"cell_id","EXPRESSION":"{{result.cell.id}}"}],"FROM":[],"WHERE":[["{{result.t}}","==",2008]],"GROUP_BY":[{"ID":"cell_id"},{"ID":"x","EXPRESSION":"{{result.x}}","ALL_VALUES":true,"AS_HISTOGRAM":true,"CONTEXT":{"WHERE":[["{{result.t}}","==",2008]]}}],"ORDER_BY":[]}}],"WHERE":[],"GROUP_BY":[{"ID":"x","EXPRESSION":"{{inner.x}}"}],"ORDER_BY":[],"SELECT_GROUP_BY":true}]}}]
        '''
        import simplejson as json
        request_defs = json.loads(requests_json)

        results = {}
        for request_def in request_defs:
            if request_def['REQUEST'] == 'execute_keyed_queries':
                formatted_parms = {}
                for k, v in request_def['PARAMETERS'].items():
                    formatted_parms[str(k)] = v
                    
                results[request_def['ID']] = services.execute_keyed_queries(
                        project = project,
                        **formatted_parms
                        )
        print "r is: ", json.dumps(results, indent=2)


if __name__ == '__main__':
    unittest.main()
