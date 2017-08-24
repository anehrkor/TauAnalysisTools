#!/usr/bin/env python

import os

import argparse

parser = argparse.ArgumentParser("Script that produces a directory and script(s) for BDT training(s)")

parser.add_argument("-s", "--inputSignal", required=True, help="Full path to signal input file.")
parser.add_argument("-b", "--inputBackground", required=True, help="Full path to background input file.")
parser.add_argument("-o", "--outputDir", required=True, help="Path where training config is written to and where the training should be executed from.")

args = parser.parse_args()

inputFilesSignal = args.inputSignal
inputFilesBackground = args.inputBackground
outputFilePath = args.outputDir

mvaDiscriminators = {
	'mvaIsolation3HitsDeltaR05opt1aLTDB' : {
		'applyPtReweighting'  : True,
		'applyEtaReweighting' : True,
		'reweight'            : 'min:KILL',
		'mvaTrainingOptions'  : "!H:!V:NTrees=1000:BoostType=Grad:Shrinkage=0.20:UseBaggedBoost:GradBaggingFraction=0.5:SeparationType=GiniIndex:nCuts=500:PruneMethod=NoPruning:MaxDepth=5",
		'inputVariables'      : [
			'TMath::Log(TMath::Max(1., recTauPt))/F',
			'TMath::Abs(recTauEta)/F',
			'TMath::Log(TMath::Max(1.e-2, chargedIsoPtSum))/F',
			'TMath::Log(TMath::Max(1.e-2, neutralIsoPtSum))/F',
			'TMath::Log(TMath::Max(1.e-2, puCorrPtSum))/F',
			'TMath::Log(TMath::Max(1.e-2, photonPtSumOutsideSignalCone))/F',
			'recTauDecayMode/I',
			'TMath::Min(30., recTauNphoton)/F',
			'TMath::Min(0.5, recTauPtWeightedDetaStrip)/F',
			'TMath::Min(0.5, recTauPtWeightedDphiStrip)/F',
			'TMath::Min(0.5, recTauPtWeightedDrSignal)/F',
			'TMath::Min(0.5, recTauPtWeightedDrIsolation)/F',
			'TMath::Min(1., recTauEratio)/F',
			'TMath::Sign(+1., recImpactParam)/F',
			'TMath::Sqrt(TMath::Abs(TMath::Min(1., TMath::Abs(recImpactParam))))/F',
			'TMath::Min(10., TMath::Abs(recImpactParamSign))/F',
			'TMath::Sign(+1., recImpactParam3D)/F',
			'TMath::Sqrt(TMath::Abs(TMath::Min(1., TMath::Abs(recImpactParam3D))))/F',
			'TMath::Min(10., TMath::Abs(recImpactParamSign3D))/F',
			'hasRecDecayVertex/I',
			'TMath::Sqrt(recDecayDistMag)/F',
			'TMath::Min(10., recDecayDistSign)/F',
			'TMath::Max(-1.,recTauGJangleDiff)/F'
		],
		'spectatorVariables'  : [
			'leadPFChargedHadrCandPt/F',
			'numOfflinePrimaryVertices/I',
			'genVisTauPt/F',
			'genTauPt/F',
			'byIsolationMVArun2v1DBoldDMwLTraw',
			'byIsolationMVArun2v1DBoldDMwLTraw2016'
		]
	}
}

execDir = "%s/bin/%s/" % (os.environ['CMSSW_BASE'], os.environ['SCRAM_ARCH'])
executable_trainTauIdMVA = execDir + 'trainTauIdMVA'
configFile_trainTauIdMVA = 'trainTauIdMVA_CMSPOS2017_cfg.py'

# create outputFilePath in case it does not yet exist
def createFilePath_recursively(filePath):
	filePath_items = filePath.split('/')
	currentFilePath = "/"
	for filePath_item in filePath_items:
		currentFilePath = os.path.join(currentFilePath, filePath_item)
		if len(currentFilePath) <= 1:
			continue
		if not os.path.exists(currentFilePath):
			os.mkdir(currentFilePath)

if not os.path.isdir(outputFilePath):
	print "outputFilePath does not yet exist, creating it."
	createFilePath_recursively(outputFilePath)

def getStringRep_bool(flag):
	retVal = None
	if flag:
		retVal = "True"
	else:
		retVal = "False"
	return retVal

print "Info: building config files for MVA training"
# also write commands to execute training into a file for convenience
trainingCommandsFileName = os.path.join(outputFilePath, "trainingCommands.txt")
trainingCommandsFile = open (trainingCommandsFileName, "w")

for discriminator in mvaDiscriminators.keys():

	print "processing discriminator = %s" % discriminator
	#----------------------------------------------------------------------------    
	# build config file for actual MVA training
	outputFileName = os.path.join(outputFilePath, "trainTauIdMVA_%s.root" % discriminator)
	print " outputFileName = '%s'" % outputFileName

	cfgFileName_original = configFile_trainTauIdMVA
	cfgFileName = os.path.join(outputFilePath, cfgFileName_original.replace("_cfg.py", "_%s_cfg.py" % discriminator))
	print " cfgFileName = '%s'" % cfgFileName
	config = "import FWCore.ParameterSet.Config as cms\n"
	config += "import os\n\n"
	config += "process = cms.PSet()\n\n"
	config += "process.fwliteInput = cms.PSet(\n"
	config += "	fileNames = cms.vstring(),\n"
	config += "	maxEvents = cms.int32(-1),\n"
	config += "	outputEvery = cms.uint32(100000)\n"
	config += ")\n\n"
	config += "process.fwliteInput.fileNames = cms.vstring(\n"
	config += "	'%s',\n" % inputFilesSignal
	config += "	'%s'\n" % inputFilesBackground
	config += ")\n\n"
	config += "process.trainTauIdMVA = cms.PSet(\n"
	config += "	treeName = cms.string('reweightedTauIdMVATrainingNtuple'),\n\n"
	config += "	signalSamples = cms.vstring('signal'),\n"
	config += "	backgroundSamples = cms.vstring('background'),\n\n"
	config += "	applyPtReweighting = cms.bool(%s),\n" % getStringRep_bool(mvaDiscriminators[discriminator]['applyPtReweighting'])
	config += "	applyEtaReweighting = cms.bool(%s),\n" % getStringRep_bool(mvaDiscriminators[discriminator]['applyEtaReweighting'])
	config += "	reweight = cms.string('%s'),\n\n" % mvaDiscriminators[discriminator]['reweight']
	config += "	branchNameEvtWeight = cms.string('evtWeight'),\n\n"
	config += "	applyEventPruning = cms.int32(0),\n\n"
	config += "	mvaName = cms.string('%s'),\n" % discriminator
	config += "	mvaMethodType = cms.string('BDT'),\n"
	config += "	mvaMethodName = cms.string('BDTG'),\n"
	config += "	mvaTrainingOptions = cms.string('%s'),\n\n" % mvaDiscriminators[discriminator]['mvaTrainingOptions']
	config += "	inputVariables = cms.vstring(\n"
	for index, inputVariable in enumerate(mvaDiscriminators[discriminator]['inputVariables']):
		if index != len(mvaDiscriminators[discriminator]['inputVariables']) - 1:
			config += "		'%s',\n" % inputVariable
		else:
			config += "		'%s'\n" % inputVariable
	config += "	),\n"
	config += "	spectatorVariables = cms.vstring(\n"
	for index, spectatorVariable in enumerate(mvaDiscriminators[discriminator]['spectatorVariables']):
		if index != len(mvaDiscriminators[discriminator]['spectatorVariables']) - 1:
			config += "		'%s',\n" % spectatorVariable
		else:
			config += "		'%s'\n" % spectatorVariable
	config += "	),\n"
	config += "	outputFileName = cms.string('%s')\n" % outputFileName
	config += ")\n\n"
	configFile = open(cfgFileName, "w")
	configFile.write(config)
	configFile.close()

	logFileName = cfgFileName.replace("_cfg.py", ".log")

	print "\nTo run the training with name %s, execute the following command:\n" % discriminator
	trainingCommand = "nice " + executable_trainTauIdMVA + " " + cfgFileName + " &> " + logFileName + "\n"
	trainingCommandsFile.write(trainingCommand+"\n")
	print "\t" + trainingCommand

print "\nAll training commands have been written to the following file as well:"
print "\t" + trainingCommandsFileName
