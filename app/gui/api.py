from flask_restful import Api, Resource
from flask_restful import reqparse
from flask import jsonify, json, request

import sys
import os
import traceback
import numpy as np
import subprocess
from pprint import pprint

from bayescmd.bcmdModel import signalGenerator, ModelBCMD
import bayescmd.jsonParsing as jsonParsing

from app import app
from app import mongo

api = Api(app)


class AvailableModels(Resource):

    def get(self):
        try:
            guidir = os.path.abspath(os.path.dirname(
                os.path.dirname(__file__)))
            assert os.path.basename(
                guidir) == 'app', "Incorrect base directory"
            build_dir = os.path.abspath(os.path.join(os.path.dirname(guidir),
                                                     'build'))
            assert os.path.basename(
                build_dir) == 'build', "Incorrect base directory"
            model_choices = [{"id": idx, "model": os.path.splitext(file)[0]}
                             for idx, file in enumerate(os.listdir(build_dir))
                             if file.endswith('.model')]

            return {"models": model_choices, "count": len(model_choices)}
        except Exception as e:
            return {"error": str(e)}


class AvailableModelDefs(Resource):

    def get(self):
        try:
            guidir = os.path.abspath(os.path.dirname(
                os.path.dirname(__file__)))
            examples_dir = os.path.abspath(os.path.join(os.path.dirname(guidir),
                                                        'examples'))
            assert os.path.basename(
                examples_dir) == 'examples', "Incorrect directory"
            model_choices = [{"id": idx, "model": os.path.splitext(file)[0]}
                             for idx, file in enumerate(os.listdir(examples_dir))
                             if file.endswith('.modeldef')]

            return {"models": model_choices, "count": len(model_choices)}
        except Exception as e:
            return{"error": str(e)}


class ModelInfo(Resource):

    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('model_name',
                                type=str,
                                help="Name of the model to POST to database.",
                                required=True)
            args = parser.parse_args()

            _modelName = args['model_name']

            model_json = {"model_name": _modelName}

            with app.app_context():
                if mongo.db.models.find(model_json).count() > 0:
                    return {"message": "Model already exists"}, 250
                else:
                    fpath = jsonParsing.getDefaultFilePath(
                        model_json['model_name'])
                    mongo.db.models.insert(jsonParsing.modeldefParse(fpath))
                    print(jsonParsing.modeldefParse(fpath))
                    return {"message": "Added Model Data"}, 200

        except Exception as e:
            return {"error": str(e)}, 404

    def get(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('model_name',
                                type=str,
                                help="Name of the model to GET from database.")
            args = parser.parse_args()

            _modelName = args['model_name']
            with app.app_context():
                model_info = mongo.db.models.find_one(
                    {"model_name": _modelName})
                model_info.pop("_id")
            return jsonify(model_info)
        except Exception as e:
            return {"error": str(e)}


class DemandCreator(Resource):

    @staticmethod
    def request_handler(request):
        # Convert from JSON string to dict using flask.json.loads
        request = json.loads(request)
        parsedReq = {}
        parsedReq['start'] = request["startTime"]
        parsedReq['end'] = request["endTime"]
        parsedReq['sample_rate'] = request["sampleRate"]
        parsedReq['peaks'] = []
        for peak in request['peaks']:
            length = float(peak['end']) - float(peak['start'])
            i = 1
            parsedReq['peaks'].append(
                (float(peak['start']),
                 float(peak['end']),
                 float(peak['height']),
                 peak['type']))
            if 'nRepeats' in peak.keys():
                while (i < int(peak['nRepeats']) and
                       parsedReq['peaks'][i - 1][1] +
                       float(peak['interval']) < request["endTime"]):
                    newStart = parsedReq['peaks'][
                        i - 1][1] + float(peak['interval'])
                    newEnd = newStart + length
                    parsedReq['peaks'].append((newStart,
                                               newEnd,
                                               float(peak['height']),
                                               peak['type']))
                    i += 1
        return parsedReq

    def get(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('demand_dict',
                                help="Dictionary of demand information.")
            args = parser.parse_args()

            with app.app_context():
                response = {"demand_signal": []}
                parsedReq = self.request_handler(args['demand_dict'])
                response["demand_signal"] = signalGenerator(
                    **parsedReq).tolist()
                print(response["demand_signal"], file=sys.stderr)
            return jsonify(response)

        except Exception as e:
            return {"error": str(e)}, 404


class RunModel(Resource):

    @staticmethod
    def request_handler(modelName, inputs, times, params, outputs, burn_in):

        if inputs is not None:
            parsed_inputs = {'names': inputs.keys()}
            parsed_inputs['values'] = np.transpose(list(inputs.values()))
        else:
            parsed_inputs = None

        if outputs is not None:
            parsed_outputs = [k for k, v in outputs.items() if v['include']]
        else:
            parsed_outputs = None

        # Handle empty params dict
        if len(params.keys()) == 0:
            params = None
        try:
            burn_in = float(burn_in)
            model = ModelBCMD(modelName,
                              inputs=parsed_inputs,
                              params=params,
                              times=[float(x) for x in times],
                              outputs=parsed_outputs,
                              burn_in=burn_in,
                              debug=False)
        except (TypeError, ValueError):
            model = ModelBCMD(modelName,
                              inputs=parsed_inputs,
                              params=params,
                              times=[float(x) for x in times],
                              outputs=parsed_outputs,
                              debug=False)

        return model

    def post(self):
        try:
            json_data = request.get_json(force=True)

            modelName = json_data['modelName']
            times = json_data['times']

            try:
                inputs = json_data['inputs']
            except KeyError:
                inputs = None
            try:
                params = json_data['params']
            except KeyError:
                params = None
            try:
                outputs = json_data['outputs']
            except KeyError:
                outputs = None
            try:
                burn_in = json_data['burnIn']
            except KeyError:
                burn_in = None

            with app.app_context():
                model = self.request_handler(modelName,
                                             inputs,
                                             times,
                                             params,
                                             outputs,
                                             burn_in)
                model.create_initialised_input()
                model.run_from_buffer()
                output = model.output_parse()

                return jsonify(output)
        except Exception as error:
            traceback.print_exc()
            return {"error": str(error)}, 404


class RunDefault(Resource):

    @staticmethod
    def request_handler(modelName, inputs, times):

        if inputs is not None:
            parsed_inputs = {'names': inputs.keys()}
            parsed_inputs['values'] = np.transpose(list(inputs.values()))
        else:
            parsed_inputs = None

        model = ModelBCMD(modelName,
                          inputs=parsed_inputs,
                          times=[float(x) for x in times],
                          debug=False)

        return model

    def post(self):
        try:

            json_data = request.get_json(force=True)
            modelName = json_data['modelName']
            try:
                inputs = json_data['inputs']
            except KeyError:
                inputs = None
            times = json_data['times']


            with app.app_context():
                model = self.request_handler(modelName,
                                             inputs,
                                             times)
                model.create_default_input()
                model.run_from_buffer()
                output = model.output_parse()
                return jsonify(output)

        except Exception as error:
            traceback.print_exc()
            return {"error": str(error)}, 404

class RunSteadyState(Resource):

    @staticmethod
    def steady_state_input(input, default, max_val, min_val):
        """
        Function to create a steady state signal for a specific input
        :param input: Name of input variable to vary
        :type input: str
        :param default: Default value of input
        :type default: float
        :param max: Max value to step up to
        :type max: float
        :param min: Min value to step down to
        :type min: float
        :return: Output signal in form required for model run
        :rtype: dict
        """
        steady_input = {'names': input}
        if (min == default) or (min > default):
            steady_input['values'] = np.concatenate((np.linspace(default, max_val, 50),
                                                     np.linspace(max_val, default, 50)))
        elif min < default:
            steady_input['values']=np.concatenate(
                            (np.linspace(default, max_val, 50),
                            np.linspace(max_val, default, 50),
                            np.linspace(default, min_val, 50),
                            np.linspace(min_val, default, 50)))

    @staticmethod
    def request_handler(modelName, input, default, max_val, min_val, params={}):

        inputs = self.steady_state_input(input, default, max_val, min_val)

        if len(params.keys()) == 0:
            params = None

        model = ModelBCMD(modelName,
                          inputs=inputs,
                          times=[float(x) for x in np.arange(0,len(inputs['values'])+100, 100)],
                          params=params,
                          debug=False)

        return model

    def post(self):
        try:

            json_data = request.get_json(force=True)
            modelName = json_data['modelName']
            try:
                inputs = json_data['inputs']
            except KeyError:
                inputs = None
            times = json_data['times']


            with app.app_context():
                model = self.request_handler(modelName,
                                             inputs,
                                             times)
                model.create_default_input()
                model.run_from_buffer()
                output = model.output_parse()
                return jsonify(output)

        except Exception as error:
            traceback.print_exc()
            return {"error": str(error)}, 404

class CompileModel(Resource):

    def get(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('model_name',
                                type=str,
                                help="Name of the model to compile.",
                                required=True)
            args = parser.parse_args()

            with app.app_context():
                result = subprocess.run(["make",
                                         "build/%s.model" % (args.model_name)],
                                        stdout=subprocess.PIPE)
                print(str(result.stdout))
                return {"stdout": str(result.stdout)}
        except Exception as error:
            traceback.print_exc()
            return {"error": str(error)}, 404
