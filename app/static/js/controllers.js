'use strict';
myApp.controller('DisplayModelsController', ['$scope', '$http',

    function($scope, $http) {

        $scope.data = {
            choice: null,
            models: available_models.models
        };

        $scope.submit = function() {
            var name = $scope.data.choice.model;
            console.log("Name is " + name);
            $http.get('/api/modelinfo', {
                "params": {
                    "model_name": name
                }
            }).then(function(response) {
                $scope.infoCategories = [{
                        "name": "Inputs",
                        "data": response.data.input
                    },
                    {
                        "name": "Outputs",
                        "data": response.data.output
                    },
                    {
                        "name": "Parameters",
                        "data": response.data.params
                    }
                ];
            });

        };
    }
]);


myApp.controller('IndexController', ['$scope', '$http', function($scope, $http) {

}]);

myApp.controller('ChooseModelController', ['$scope', '$http', 'RunModelData',

    function($scope, $http, RunModelData) {

        $scope.data = {
            choice: null,
            models: available_models.models
        };

        //Define functions

        $scope.chooseModel = function() {
            var name = $scope.data.choice.model;
            console.log("Name is " + name);
            RunModelData.setModel(name);
        };
    }
]);

myApp.controller('CsvFileController', ['$scope', '$http', '$parse', '$window', 'RunModelData',
    function($scope, $http, $parse, $window, RunModelData) {
        // Define initial variables.
        $scope.data = {
            inputHeader: {},
            inputKeys: [],
            inputs: {},
            outputHeader: {},
            outputKeys: [],
            outputs: {}
        };
        $scope.parseResult = null;
        $scope.inputsLength = Object.keys($scope.data.inputHeader).length;
        $scope.outputsLength = Object.keys($scope.data.outputHeader).length;
        $scope.inputSaved = "";
        $scope.outputSaved = "";
        // Define functions.

        $scope.$watchCollection("parseResult", function(newResult, oldResult) {
            $scope.data.inputHeader = {};
            $scope.data.inputs = {};
            $scope.data.outputHeader = {};
            $scope.data.outputs = {};
            console.log("Getting data after file change");
            $scope.getState();
            console.log($scope.data);
        });

        $scope.$watchCollection("data", function(newData, oldData) {
            $scope.inputsLength = Object.keys(newData.inputHeader).length;
            $scope.outputsLength = Object.keys(newData.outputHeader).length;
        });

        $scope.setInputs = function() {
            if (Object.keys($scope.data.inputHeader).length !== 0) {
                $scope.data.inputs = setObject($scope.parseResult, $scope.data.inputHeader);
                $scope.data.inputKeys = Object.keys($scope.data.inputs);
                $scope.inputSaved = "Input Saved!";
            } else {
                $scope.inputSaved = "No inputs selected"
            }
        };

        $scope.setOutputs = function() {
            if (Object.keys($scope.data.outputHeader).length !== 0) {
                $scope.data.outputs = setObject($scope.parseResult, $scope.data.outputHeader);
                $scope.data.outputKeys = Object.keys($scope.data.outputs);
                $scope.outputSaved = "Output Saved!";
            } else {
                $scope.outputSaved = "No outputs selected"
            }
        };

        $scope.getState = function() {
            $scope.data = RunModelData.getState();
        };

        $scope.saveState = function() {
            RunModelData.setKey($scope.data.inputs, "inputs");
            RunModelData.setKey($scope.data.outputs, "outputs");
            RunModelData.setKey($scope.data.inputHeader, "inputHeader");
            RunModelData.setKey($scope.data.outputHeader, "outputHeader");
            RunModelData.setKey($scope.data.inputKeys, "inputKeys");
            RunModelData.setKey($scope.data.outputKeys, "outputKeys");
        };

        // Start of running code.
        // Get inputs and outputs from checkboxes. Get lengths of each for logic checks
        $scope.getState();
        console.log($scope.data);
        // plotCSV($scope.data.inputs);


    }
]);

myApp.controller('TimeCreationController', ['$scope', '$http', '$parse', 'RunModelData', 'PeakTypes',
    function($scope, $http, $parse, RunModelData, PeakTypes) {

        // Define objects
        $scope.time = {
            "startTime": 0,
            "endTime": undefined,
            "sampleRate": 1,
        };
        $scope.timeNeeded = true;
        $scope.timeSignal = [];
        $scope.timeSignalSample = [];
        // Define functions
        $scope.getState = function() {
            $scope.data = RunModelData.getState();
            $scope.timeNeeded = !$scope.data.inputs.hasOwnProperty('t');
            console.log($scope.data);
        };

        $scope.saveState = function() {
            console.log("SAVING STATE");
            console.log($scope.data);
            RunModelData.setKey($scope.data.inputs, "inputs");
            RunModelData.setKey($scope.data.outputs, "outputs");
            RunModelData.setKey($scope.data.inputHeader, "inputHeader");
            RunModelData.setKey($scope.data.outputHeader, "outputHeader");
        };

        $scope.generateTime = function() {
            $scope.timeSignal = _.range($scope.time.startTime,$scope.time.endTime,$scope.time.sampleRate);
            console.log($scope.timeSignal);
            $scope.timeSignalSample = $scope.timeSignal.slice(0, parseInt($scope.timeSignal.length/10));
        };

        $scope.confirmTime = function() {
            $scope.data.inputs['t'] = $scope.timeSignal;
            $scope.inputHeader.push['t'];
        };

        $scope.getState();

    }
]);

myApp.controller('DemandCreationController', ['$scope', '$http', '$parse', 'RunModelData', 'PeakTypes',
    function($scope, $http, $parse, RunModelData, PeakTypes) {

        // Define objects
        $scope.demand = {
            "startTime": 0,
            "endTime": "undefined",
            "sampleRate": "undefined",
            "peaks": []
        };
        $scope.peaks = PeakTypes.getPeaks();
        $scope.demandNeeded = true;
        $scope.demandSignal = {
            "time": []
        };
        $scope.repeat = false;

        //} Define functions
        $scope.getState = function() {
            $scope.data = RunModelData.getState();
            $scope.demandNeeded = !$scope.data.inputs.hasOwnProperty('u');
            console.log("REPEAT? " + $scope.demandNeeded)
            console.log($scope.data);
            $scope.demand.endTime = $scope.data.inputs.t[$scope.data.inputs.t.length - 1];
            $scope.demand.sampleRate = $scope.data.inputs.t[1] - $scope.data.inputs.t[0];
        };
        $scope.saveState = function() {
            console.log("SAVING STATE");
            console.log($scope.data);
            RunModelData.setKey($scope.data.inputs, "inputs");
            RunModelData.setKey($scope.data.outputs, "outputs");
            RunModelData.setKey($scope.data.inputHeader, "inputHeader");
            RunModelData.setKey($scope.data.outputHeader, "outputHeader");
        };


        $scope.addNewChoice = function() {
            var newItemNo = $scope.demand.peaks.length + 1;
            $scope.demand.peaks.push({
                'id': 'peak' + newItemNo
            });
        };

        $scope.removeChoice = function() {
            var lastItem = $scope.demand.peaks.length - 1;
            $scope.demand.peaks.splice(lastItem);
        };

        $scope.getDemandTrace = function() {
            console.log($scope.demand);
            $http.get('/api/demandcreation', {
                    "params": {
                        "demand_dict": $scope.demand
                    }
                }).then(function(response) {
                    console.log(response);
                    $scope.demandSignal.demand = response.data.demand_signal;
                    for (var i = $scope.demand.startTime; i <= $scope.demand.endTime; i += $scope.demand.sampleRate) {
                        $scope.demandSignal.time.push(i);
                    }
                    console.log($scope.demandSignal);
                })
                .catch(function(data) {
                    console.log(data);
                    $scope.response = data;
                });
        };

        $scope.confirmDemand = function() {
            $scope.data.inputs['u'] = $scope.demandSignal.demand;
            $scope.inputHeader.push['u'];
        }

        $scope.getState();

    }
]);

myApp.controller('ParameterController', ['$scope', '$http', '$parse', 'RunModelData',
    function($scope, $http, $parse) {
        //} Define functions
        $scope.getState = function() {
            $scope.data = RunModelData.getState();
            console.log($scope.data);
        };

        $scope.saveState = function() {
            console.log("SAVING STATE");
            console.log($scope.data);
            RunModelData.setKey($scope.data.inputs, "inputs");
            RunModelData.setKey($scope.data.outputs, "outputs");
            RunModelData.setKey($scope.data.inputHeader, "inputHeader");
            RunModelData.setKey($scope.data.outputHeader, "outputHeader");
        };

        $scope.getDefaultParameters = function() {

        };

        // Running code

        $scope.getState();
    }
]);


myApp.controller('ModelCheckController', ['$scope', '$http', '$parse', 'RunModelData',
    function($scope, $http, $parse) {
        //} Define functions
        $scope.getState = function() {
            $scope.data = RunModelData.getState();
            console.log($scope.data);
        };

        $scope.saveState = function() {
            console.log("SAVING STATE");
            console.log($scope.data);
            RunModelData.setKey($scope.data.inputs, "inputs");
            RunModelData.setKey($scope.data.outputs, "outputs");
            RunModelData.setKey($scope.data.inputHeader, "inputHeader");
            RunModelData.setKey($scope.data.outputHeader, "outputHeader");
        };

        // Running code

        $scope.getState();
    }
]);
