mkdir -p result
text2workspace.py datacard.txt -o workspace.root --channel-masks| tee result/workspace.out

#Profile likelihood on Asimov dataset
combine workspace.root -M MultiDimFit \
   -n _ttbar_exp \
   --algo grid \
   --points 100 \
   -t -1 --expectSignal=1 \
   --saveFitResult \
   --setParameterRanges r=0.8,1.2 \
   | tee result/combine_exp_log.out

#Profile likelihood on observed data
combine workspace.root -M MultiDimFit \
  -n _ttbar_obs \
  --algo grid \
  --points 100 \
  --saveFitResult \
  --setParameterRanges r=0.8,1.2 \
 | tee result/combine_obs_log.out

	
mv higgsCombine_ttbar_exp.MultiDimFit.mH120.root result/likelihood_exp.root
mv higgsCombine_ttbar_obs.MultiDimFit.mH120.root result/likelihood_obs.root

#Plot the likelihood scan
plot1DScan.py result/likelihood_exp.root -o result/likelihood_exp --main-label "Stat."  --y-max 3 --y-cut 40| tee result/plot1DScan_exp.out
plot1DScan.py result/likelihood_obs.root -o result/likelihood_obs --main-label "Stat."  --y-max 3 --y-cut 40| tee result/plot1DScan_obs.out

rm -f combine_logger.out
mv workspace.root result/

#Plot the impacts for the Asimov Dataset
combineTool.py -M Impacts -d result/workspace.root -m 125 --doInitialFit --robustFit 1 -t -1 --expectSignal=1 | tee -a result/combine_exp_log.out
combineTool.py -M Impacts -d result/workspace.root -m 125 --robustFit 1 --doFits --parallel 30 -t -1 --expectSignal=1  | tee -a result/combine_exp_log.out
combineTool.py -M Impacts -d result/workspace.root -m 125 -o result/impacts_exp.json -t -1 --expectSignal=1 | tee -a result/combine_exp_log.out
plotImpacts.py -i result/impacts_exp.json -o result/impact_exp | tee -a result/combine_exp_log.out

#Plot the impacts for the observed data
combineTool.py -M Impacts -d result/workspace.root -m 125 --doInitialFit --robustFit 1  | tee -a result/combine_obs_log.out
combineTool.py -M Impacts -d result/workspace.root -m 125 --robustFit 1 --doFits --parallel 30   | tee -a result/combine_obs_log.out
combineTool.py -M Impacts -d result/workspace.root -m 125 -o result/impacts_obs.json  | tee -a result/combine_obs_log.out
plotImpacts.py -i result/impacts_obs.json -o result/impact_obs | tee -a result/combine_obs_log.out

rm higgsCombine*
mv combine_logger.out result/
