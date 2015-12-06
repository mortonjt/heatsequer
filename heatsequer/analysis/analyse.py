#!/usr/bin/env python


"""
heatsequer analysis module
"""

# amnonscript

__version__ = "0.9"

import heatsequer as hs

import numpy as np
import matplotlib as mpl
mpl.use('Qt4Agg')
import matplotlib.pyplot as plt
from matplotlib.pyplot import *
import sklearn.metrics
import sklearn.cross_validation


def getdiffsigall(expdat,field,val1,val2=False,numperm=1000,maxfval=0.1):
	"""
	Get the differentially abundant bacteria (using getdiffsig) using all methods possible.
	Sort results according to combined effect order
	input:
	see getdiffsig()

	output:
	newexp - the new experiment with bacteria significantly differentiating the 2 groups by at least 1 method
	"""

	methods=['mean','binary','ranksum','freqpres']
	res=[]
	for cmethod in methods:
		res.append(hs.getdiffsig(expdat,field=field,val1=val1,val2=val2,method=cmethod,numperm=numperm,maxfval=maxfval))

	keep=[]
	keeporder=[]
	for cidx,cseq in enumerate(expdat.seqs):
		pos=[]
		for cres in res:
			if cseq in cres.seqdict:
				pos.append(float(cres.seqdict[cseq])/len(cres.seqs))
		if len(pos)>0:
			keep.append(cidx)
			keeporder.append(np.mean(pos))
	keep=np.array(keep)
	if len(keep)>0:
		si=np.argsort(keeporder)
		newexp=hs.reorderbacteria(expdat,keep[si])
		newexp.filters.append('differential expression (all) in %s between %s and %s' % (field,val1,val2))
		hs.addcommand(newexp,"getdiffsigall",params=params,replaceparams={'expdat':expdat})
		return newexp
	else:
		hs.Debug(6,'No bacteria found')
		return False


def getdiffsig(expdat,field,val1,val2=False,method='mean',numperm=1000,maxfval=0.1):
	"""
	test the differential expression between 2 groups (val1 and val2 in field field)
	for bacteria that have a high difference.
	input:
	expdat
	field - the field for the 2 categories
	val1 - values for the first group
	val2 - value for the second group or false to compare to all other
	method - the test to compare the 2 groups:
		mean - absolute difference in mean frequency
		binary - abs diff in binary presence/absence
		ranksum - abs diff in rank order (to ignore outliers)
		freqpres - abs diff in frequency only in samples where bacteria is present
	numperm - number of random permutations to run
	maxfval - the maximal f-value (FDR) for a bacteria to keep

	output:
	newexp - the experiment with only significant (FDR<=maxfval) difference, sorted according to difference
	"""
	params=locals()

	minthresh=2
	exp1=hs.filtersamples(expdat,field,val1,exact=True)
	if val2:
		exp2=hs.filtersamples(expdat,field,val2,exact=True)
	else:
		exp2=hs.filtersamples(expdat,field,val1,exact=True,exclude=True)
	cexp=hs.joinexperiments(exp1,exp2)
	len1=len(exp1.samples)
	len2=len(exp2.samples)
	dat=cexp.data
	dat[dat<minthresh]=minthresh
	dat=np.log2(dat)
	numseqs=len(cexp.seqs)

	eps=0.000001

	if method=='mean':
		pass
	elif method=='ranksum':
		for idx in range(numseqs):
			dat[idx,:]=stats.rankdata(dat[idx,:])
	elif method=='binary':
		dat=(dat>np.log2(minthresh))
	elif method=='freqpres':
		dat[dat<=minthresh]=np.nan
	else:
		hs.Debug(9,"Method not supported!",method)
		return


	m1=np.nanmean(dat[:,0:len1],axis=1)
	m2=np.nanmean(dat[:,len1:],axis=1)
	odif=(m1-m2)/(m1+m2+eps)
	odif[np.isnan(odif)]=0
	alldif=np.zeros([len(cexp.sids),numperm])
	for x in range(numperm):
		rp=np.random.permutation(len1+len2)
		m1=np.nanmean(dat[:,rp[0:len1]],axis=1)
		m2=np.nanmean(dat[:,rp[len1:]],axis=1)
		diff=(m1-m2)/(m1+m2+eps)
#		diff[np.isnan(diff)]=0
		alldif[:,x]=diff
	pval=[]
	for crow in range(len(odif)):
		cdat=alldif[crow,:]
		cdat=cdat[np.logical_not(np.isnan(cdat))]
		cnumperm=len(cdat)
		if cnumperm==0:
			pval.append(1)
			continue
		cpval=float(np.sum(np.abs(cdat)>=np.abs(odif[crow])))/cnumperm
		# need to remember we only know as much as the number of permutations - so add 1 as upper bound for fdr
		cpval=min(cpval+(1.0/cnumperm),1)
		pval.append(cpval)
	# NOTE: maybe use better fdr (this one not tested...)
	fval=hs.fdr(pval)
	keep=np.where(np.array(fval)<=maxfval)
	seqlist=[]
	for cidx in keep[0]:
		seqlist.append(cexp.seqs[cidx])
	newexp=hs.filterseqs(expdat,seqlist)
	odif=odif[keep[0]]
	sv,si=hs.isort(odif)
	newexp=hs.reorderbacteria(newexp,si)
	hs.addcommand(newexp,"getdiffsigall",params=params,replaceparams={'expdat':expdat})
	newexp.filters.append('differential expression (%s) in %s between %s and %s' % (method,field,val1,val2))
	return newexp


def bicluster(expdat,numiter=5,startb=False,starts=False,method='zscore',sampkeep=0.5,bactkeep=0.25,justcount=False,numruns=1):
	"""
	EXPERIMENTAL
	cluster bacteria and samples from subgroup
	input:
	expdat
	numiter - number of iterations to run the biclustering
	startb - start list of bacteria [acgt] of False for random
	method: the method for choosing which sample/bacteria to keep. options areL
		'zscore'
		'ranksum'
		'binary' - only one working currently!!!
	sampkeep - the minimal fraction of bacteria to be present in a sample in order to keep the sample (for binary) or 0 for random
	bactkeep - the minimal difference in the number of samples a bacteria apprears in order to keep the bacteria (for binary) or 0 for random
	justcount - True to not reorder the experiment - just the bacteria & samples (to run faster)
	numruns - number of times to run

	output:
	newexp - the reordered experiment
	seqs - the sequences in the cluster
	samples - the samples in the cluster (position in experiment)
	"""

	dat=copy.copy(expdat.data)
	if method=='zscore':
		dat[dat<20]=20
		dat=np.log2(dat)
#		dat=(dat>1)
	elif method=='binary':
		dat=(dat>1)
	bdat=dat
#	bdat=scale(dat,axis=1,copy=True)
	nbact=np.size(dat,0)
	nsamp=np.size(dat,1)
	allsamp=np.arange(nsamp)
	allbact=np.arange(nbact)


	allseqs=[]
	allsamples=[]
	bthresh=0.25
	sthresh=0
	for crun in range(numruns):
		if bactkeep==0:
			bactkeep=np.random.uniform(0.1,0.5)
			au.Debug(6,"bactkeep %f" % bactkeep)
		if sampkeep==0:
			sampkeep=np.random.uniform(0.25,0.75)
			au.Debug(6,"sampkeep %f" % sampkeep)
		if startb:
			ubact=[]
			for cbact in startb:
				ubact.append(expdat.seqdict[cbact])
		else:
			ubact=[np.random.randint(nbact)]
		if starts:
			usamp=starts
		else:
			usamp=np.arange(nsamp)
		for citer in range(numiter):
			if method=='zscore':
				# find samples
				meanin=np.mean(bdat[ubact,:],axis=0)
	#			print(meanin[0:10])
				sdiff=meanin-np.mean(np.mean(bdat[ubact,:]))
	#			print(sdiff[0:10])
				if len(ubact)>1:
					usamp=allsamp[sdiff>sthresh*np.std(np.mean(bdat[ubact,:],axis=0))]
				else:
					usamp=allsamp[sdiff>sthresh*np.std(bdat[ubact,:])]
				print("num samples %d" % len(usamp))

				meanin=np.mean(dat[:,usamp],axis=1)
				nusamp=np.setdiff1d(allsamp,usamp)
				sdiff=meanin-np.mean(dat[:,nusamp],axis=1)
	#			sdiff=meanin-np.mean(np.mean(bdat[:,usamp]))
				if len(usamp)>1:
	#				ubact=allbact[sdiff>bthresh*np.std(np.mean(bdat,axis=1))]
					ubact=allbact[sdiff>bthresh]
				else:
	#				ubact=allbact[sdiff>bthresh*np.std(bdat)]
					ubact=allbact[sdiff>bthresh]
				print("num bacteria %d" % len(ubact))

			elif method=='binary':
				# find samples
				meanin=np.mean(bdat[ubact,:],axis=0)
				sdiff=meanin
				if len(ubact)>1:
					usamp=allsamp[sdiff>=sampkeep]
				else:
					usamp=allsamp[sdiff>=sampkeep]
				print("num samples %d" % len(usamp))

				meanin=np.mean(dat[:,usamp],axis=1)
				nusamp=np.setdiff1d(allsamp,usamp)
				sdiff=meanin-np.mean(dat[:,nusamp],axis=1)
				if len(usamp)>1:
	#				ubact=allbact[sdiff>bthresh*np.std(np.mean(bdat,axis=1))]
					ubact=allbact[sdiff>=bactkeep]
				else:
	#				ubact=allbact[sdiff>bthresh*np.std(bdat)]
					ubact=allbact[sdiff>=bactkeep]
				print("num bacteria %d" % len(ubact))

			elif method=='ranksum':
				nubact=np.setdiff1d(allbact,ubact)
				keepsamp=[]
				apv=[]
				astat=[]
				for idx,csamp in enumerate(expdat.samples):
					g1=bdat[ubact,idx]
					g2=bdat[nubact,idx]
					if len(g1)>1:
						g1=np.squeeze(g1)
					if len(g2)>1:
						g2=np.squeeze(g2)
					stat,pv=stats.mannwhitneyu(g2,g1)
					apv.append(pv)
					astat.append(stat)
					if pv<0.05:
						keepsamp.append(idx)
				# figure()
				# hist(apv,100)
				# show()
				# figure()
				# hist(astat,100)
				# show()
				usamp=keepsamp
				print('number of samples: %d' % len(usamp))
				nusamp=np.setdiff1d(allsamp,usamp)
				keepbact=[]
				for idx,cbact in enumerate(expdat.sids):
					g1=np.squeeze(bdat[idx,usamp])
					g2=np.squeeze(bdat[idx,nusamp])
					try:
						stat,pv=stats.mannwhitneyu(g2,g1)
						if pv<0.001:
							keepbact.append(idx)
					except:
						pass
				ubact=keepbact
				print('number of bacteria: %d' % len(ubact))

			else:
				au.Debug(9,"biclustering method %s not supported")
				return

		x=np.setdiff1d(allsamp,usamp)
		sampo=np.concatenate((usamp,x))
		bacto=np.concatenate((ubact,np.setdiff1d(allbact,ubact)))

		seqs=[]
		for cbact in ubact:
			seqs.append(expdat.seqs[cbact])
		samples=[]
		for csamp in usamp:
			samples.append(csamp)

		if not justcount:
			newexp=reordersamples(expdat,sampo)
			newexp=reorderbacteria(newexp,bacto,inplace=True)
			newexp.filters.append('biclustering')
		else:
			newexp=False

		allseqs.append(seqs)
		allsamples.append(samples)
	return newexp,allseqs,allsamples


def testbicluster(expdat,numiter=5,numruns=100):
	"""
	show the sizes of clusters in data, random and random normalized
	"""
	figure()
	cc,seqs,samps=bicluster(expdat,method='binary',justcount=True,numruns=numruns,numiter=numiter)
	for idx,cseqs in enumerate(seqs):
		plot(len(samps[idx]),len(cseqs),'xr')
	rp=randomizeexp(expdat,normalize=False)
	cc,seqs,samps=bicluster(rp,method='binary',justcount=True,numruns=numruns,numiter=numiter)
	for idx,cseqs in enumerate(seqs):
		plot(len(samps[idx]),len(cseqs),'xk')
	rp=randomizeexp(expdat,normalize=True)
	cc,seqs,samps=bicluster(rp,method='binary',justcount=True,numruns=numruns,numiter=numiter)
	for idx,cseqs in enumerate(seqs):
		plot(len(samps[idx]),len(cseqs),'xk')
	xlabel('# Samples in cluster')
	ylabel('# Bacteria in cluster')



def getexpdbsources(expdat,seqdb=False):
	'''
	EXPERIMENTAL
	predict the probable source for each bacteria
	based on the bactdb automatic bacteria database,
	by each time taking the sample with the highest number of common bacteria with the experiment
	and defining that sample as the source for these bacteria.
	input:
	expdat : Experiment
	seqdb : the bactdb automatic database ( from bactdb.load() )
	output:
	newexp : Experiment
		same as expdat, but taxonomy now modified to include predicted source for each bacteria
	'''
	params=locals()

	if not seqdb:
		if not expdat.seqdb:
			au.Debug(9,'No sequence database loaded')
			return
		else:
			seqdb=expdat.seqdb

	dat=hs.bactdb.GetDBSource(seqdb,expdat.seqs)

	newexp=hs.copyexp(expdat)

	THRESH=0.001
	used=np.arange(np.size(dat,0))
	done=False
	while not done:
		npsamp=np.sum(dat[used,:]>=THRESH,axis=0)
		pos=np.argmax(npsamp)
		print('sample is %d, size is %d' % (pos,npsamp[pos]))
		sid,sname=hs.bactdb.GetSampleStudy(expdat.seqdb,pos+1)
		print('studyid %d name %s' % (sid,sname))
		ubact=np.where(dat[used,pos]>=THRESH)[0]
		for cpos in ubact:
			newexp.tax[used[cpos]]+=sname
		used=np.setdiff1d(used,used[ubact])
		if len(used)<10:
			print('got them all')
			done=True
		if len(ubact)<=2:
			print('piti')
			done=True
		if npsamp[pos]<=2:
			print('pata')
			done=True
	newexp.filters.append("Assign sources from bactdb (max sample binary overlap)")
	hs.addcommand(newexp,"getexpdbsources",params=params,replaceparams={'expdat':expdat})
	return newexp



def BaysZeroClassifyTest(oexpdat,field,val1,val2=False,n_folds=10,istreeexpand=False,randseed=False,numiter=1):
	"""
	Test the baysian zero inflated classifier by doing n_fold cross validation on a given dataset
	input:
	expdat
	field - the field to use for classification
	val1 - the value of group1 in field
	val2 - value of group2 in field, or False to use all non val1 as group2
	n_folds - number of groups to divide to for crossvalidation
	istreeexpand - True if we want to use the tree shrinkage on each training set (if the exp is from addsubtrees)
	randseed - if non False, use the specified random seed for the test/validation division
	numiter - the number of times to run the cross validation

	output:
	auc - the auc of each iteration
	"""
	if randseed:
		np.random.seed(randseed)

	# we want only to keep the 2 classes
	if val2:
		oexpdat=filtersamples(oexpdat,field,[val1,val2])

	# remove the validation samples and keep them in a different experiment valexp
	ind1=hs.findsamples(oexpdat,field,val1)
	types=np.zeros(len(oexpdat.samples))
	types=types>10
	types[ind1]=True
	aucres=[]
	for citer in range(numiter):
		rs = sklearn.cross_validation.StratifiedKFold(types, n_folds=n_folds,shuffle=True)
		for trainidx,testidx in rs:
			valexp=hs.reordersamples(oexpdat,testidx)
			expdat=hs.reordersamples(oexpdat,trainidx)
			# classify
			lrscores=hs.BayZeroClassify(expdat,valexp,field,val1,val2,istreeexpand)

			# prepare the correct answer list
			typeis1=[]
			for vsamp in valexp.samples:
				if valexp.smap[vsamp][field]==val1:
					vtype=1
				else:
					vtype=2
				typeis1.append(vtype==1)

			cauc=sklearn.metrics.roc_auc_score(typeis1, lrscores, average='macro', sample_weight=None)
			hs.Debug(4,"auc=%f" % cauc)
			aucres.append(cauc)

	hs.Debug(8,"mean is : %f" % np.mean(aucres))
	hs.Debug(8,"s.err is : %f" % (np.std(aucres)/np.sqrt(len(aucres))))
	return(aucres)


def BayZeroClassify(expdat,valexp,field,val1,val2=False,istreeexpand=False):
	"""
	Do the Zero inflated Naive Bayes Classifier
	Does a p-value based on presence/absence if bacteria is 0 in sample, otherwise do non-parametric permutaion test p-value
	combine p-values for all bacteria as if independent and look at log ratio of 2 categories as prediction
	input:
	expdat - the training set
	valexp - the validation set (to be classified)
	field - the field to use for classification
	val1 - the value of group1 in field
	val2 - value of group2 in field, or False to use all non val1 as group2
	istreeexpand - True if we want to use the tree shrinkage on each training set (if the exp is from addsubtrees)

	output:
	pred - the log2(ratio) prediction score for each sample in the validation experiment (>0 means from val1, <0 means from val2)
	"""

	# if val2 is not empty, keep only samples with val1 or val2
	if val2:
		expdat=hs.filtersamples(expdat,field,[val1,val2])
	ind1=hs.findsamples(expdat,field,val1)
	types=np.zeros(len(expdat.samples))
	types=types>10
	types[ind1]=True

	# if an expanded tree, keep the best subtrees
	if istreeexpand:
		expdat=hs.keeptreebest(expdat,field,val1,val2)
		valexp=hs.filterseqs(valexp,expdat.seqs)

	# prepare the claissifier
	g1ind=hs.findsamples(expdat,field,val1)
	if val2:
		g2ind=hs.findsamples(expdat,field,val2)
	else:
		g2ind=hs.findsamples(expdat,field,val1,exclude=True)

	tot1=len(g1ind)
	tot2=len(g2ind)
	dat=expdat.data
	zero1=np.sum(dat[:,g1ind]==0,axis=1)
	zero2=np.sum(dat[:,g2ind]==0,axis=1)

	# p value for getting a 0 in each sample type
	# we do max(zero1,1) to remove effect of sampling error
	MINTHRESH=1
	pmissing1=np.divide((np.maximum(MINTHRESH,zero1)+0.0),tot1)
	pmissing2=np.divide((np.maximum(MINTHRESH,zero2)+0.0),tot2)

	ppres1=np.divide((np.maximum(MINTHRESH,tot1-zero1)+0.0),tot1)
	ppres2=np.divide((np.maximum(MINTHRESH,tot2-zero2)+0.0),tot2)
	# and the log ratio of proability 1 to probability 2
	lograt0=np.log2(pmissing1/pmissing2)
	logratn0=np.log2(ppres1/ppres2)

	# the prediction log ratio scores
	lrscores=[]
	for vidx,vsamp in enumerate(valexp.samples):
		au.Debug(2,"Classifying sample %s" % vsamp)
		cvdat=valexp.data[:,vidx]
		vzero=np.where(cvdat==0)[0]
		crat0=np.sum(lograt0[vzero])
		vnzero=np.where(cvdat>0)[0]
		cratn0=np.sum(logratn0[vnzero])
		# need to choose bigger or smaller (direction of test)
		# we test both and take the more extreme p-value
		# the probability to be bigger
		ratnz=[]
		for cnzpos in vnzero:
			allz=np.where(dat[cnzpos,:]>0)[0]
			nz1=np.intersect1d(allz,g1ind)
			if len(nz1)<5:
				continue
			nz2=np.intersect1d(allz,g2ind)
			if len(nz2)<5:
				continue
			d1=dat[cnzpos,nz1]
			d2=dat[cnzpos,nz2]
			p1b=(0.0+max(1,np.sum(d1>=cvdat[cnzpos])))/len(d1)
			p2b=(0.0+max(1,np.sum(d2>=cvdat[cnzpos])))/len(d2)
			ratb=np.log2(p1b/p2b)
			p1s=(0.0+max(1,np.sum(d1<=cvdat[cnzpos])))/len(d1)
			p2s=(0.0+max(1,np.sum(d2<=cvdat[cnzpos])))/len(d2)
			rats=np.log2(p1s/p2s)

			if np.abs(ratb)>=np.abs(rats):
				ratnz.append(ratb)
			else:
				ratnz.append(rats)
		cratfreq=np.sum(ratnz)
		totratio=crat0+cratfreq+cratn0+np.log2((tot1+0.0)/tot2)
		lrscores.append(totratio)
		hs.Debug(2,"LRScore %f, zscore %f, nzscore %f, freqscore %f" % (totratio,crat0,cratn0,cratfreq))
	hs.Debug(3,"Finished classifying")
	return lrscores



def keeptreebest(expdat,field,val1,val2,method="meandif"):
	"""
	EXPERIMENTAL
	keep only the best combinations wrt given criteria
	use after addsubtrees()

	input:
	expdat - after addsubtrees
	field - the field to use for comparison
	val1 - value for group1
	val2 - value for group2 or False for all except group1
	method:
		meandif - keep the largest mean difference between groups / total mean
	"""
	params=locals()

	pos1=findsamples(expdat,field,val1)
	if val2:
		pos2=findsamples(expdat,field,val2)
	else:
		pos2=findsamples(expdat,field,val1,exclude=True)
	allpos=list(set(pos1+pos2))

	mean1=np.mean(expdat.data[:,pos1],axis=1)
	mean2=np.mean(expdat.data[:,pos2],axis=1)
	meanall=np.mean(expdat.data[:,allpos],axis=1)
	minval=1.0/len(allpos)
	meanall[meanall<1.0/minval]=minval
	difval=np.abs((mean1-mean2)/meanall)

	si=np.argsort(difval)
	si=si[::-1]

	dontuse={}
	keep=[]
	for cidx in si:
		cseq=expdat.seqs[cidx]
		poss=cseq.split(',')
		if len(poss)==1:
			if not str(expdat.seqdict[cseq]) in dontuse:
				keep.append(cidx)
				dontuse[str(expdat.seqdict[cseq])]=True
			continue
		keepit=True
		for cpos in poss:
			if cpos=='':
				continue
			if cpos in dontuse:
				keepit=False
				break
		if keepit:
			keep.append(cidx)
			for cpos in poss:
				dontuse[cpos]=True
	newexp=reorderbacteria(expdat,keep)
	newexp.filters.append("keeptreebest field %s val1 %s val2 %s" % (field,val1,str(val2)))
	hs.addcommand(newexp,"keeptreebest",params=params,replaceparams={'expdat':expdat})
	return newexp


def randomizeexp(expdat,normalize=False):
	"""
	randomly permute each bacteria in the experiment indepenedently (permute the samples where it appears)
	input:
	expdat
	normalize - True to renormalize each sample to constant sum, False to not normalize

	output:
	newexp - the permuted experiment
	"""

	newexp=copyexp(expdat)
	numsamps=len(newexp.samples)
	for idx,cseq in enumerate(newexp.seqs):
		rp=np.random.permutation(numsamps)
		newexp.data[idx,:]=newexp.data[idx,rp]
	if normalize:
		newexp=hs.normalizereads(newexp,inplace=True,fixorig=False)

	newexp.filters.append("RANDOMIZED!!! normalize = %s" % normalize)
	hs.addcommand(randomizeexp,"keeptreebest",params=params,replaceparams={'expdat':expdat})
	return newexp


def testmdenrichment(expdat,samples,field,numeric=False):
	"""
	test for enrichment in a subset of samples of the experiment for metadata field field
	input:
	expdat
	samples - the samples (positions) for the enrichment testing
	field - the field to test
	numeric - True if the field is numeric (test mean)
	"""

	vals=getfieldvals(expdat,field)
	numsamps=len(vals)
	numgroup=len(samples)
	uvals=list(set(vals))
	gmap=defaultdict(list)
	for idx,cval in enumerate(vals):
		gmap[cval].append(idx)

	pv={}
	for cval in uvals:
		glen=float(len(gmap[cval]))
		numin=float(len(np.intersect1d(samples,gmap[cval])))
		pnull=glen/numsamps
		p1=stats.binom.cdf(numin,numgroup,pnull)
		p2=stats.binom.cdf(numgroup-numin,numgroup,1-pnull)
		p=min(p1,p2)
		pv[cval]={}
		pv[cval]['pval']=p
		pv[cval]['observed']=numin
		pv[cval]['expected']=pnull*numgroup

#		if p<0.05:
#			print("cval %s numin %f groupsize %d pnull %f p1 %f p2 %f" % (cval,numin,numgroup,pnull,p1,p2))

	return pv


def testmdenrichmentall(expdat,samples,maxpv=0.001,fdr=0.05):
	"""
	test enrichment in all metadata fields/values
	input:
	expdat
	samples - a list of samples to test (positions, not sample names)
	fdr - the false discovery rate in order to show a category

	output:
	upv - a list of dict of pvalues for significant fields/values ('pval','expected','observed','field','val')
	"""

	justp=[]
	allpv=[]
	for cfield in expdat.fields:
		vals=getfieldvals(expdat,cfield)
		uvals=list(set(vals))
		if len(uvals)>10:
			continue
		pv=testmdenrichment(expdat,samples,cfield)
		for k,v in pv.items():
			justp.append(v['pval'])
			v['field']=cfield
			v['val']=k
			allpv.append(v)
#			if v['pval']<=maxpv:
#				print("field %s, val %s, pv %f (observed %d, expected %f)" % (cfield,k,v['pval'],v['observed'],v['expected']))

	# do the fdr if needed
	if fdr:
		fval=au.fdr(justp)
		keep=np.where(np.array(fval)<=fdr)
		keep=keep[0]
	else:
		keep=np.arange(len(justp))

	if len(keep)==0:
		au.Debug(6,'No significant cateogries found')

	upv=[]
	for ckeep in keep:
		upv.append(allpv[ckeep])
		au.Debug(6,allpv[ckeep])

	upv=sortenrichment(upv)
	return upv



def sortenrichment(enrich,method='bidirectional',epsilon=2):
	"""
	sort an enrichment list (with 'observed', 'expected' dict values) according to effect size
	the effect size is abs(log(obs/(expected+EPS)))
	input:
	enrich - a list of dict with 'observed' abd 'expected' keys (i.e.e from testmdenrichmentall)
	method:
		bidirectional - use abs(log(o+EPS)/log(E+EPS))
		single - use log(o)/log(E)
		val - use o
	epsilon - the value used to reduce effect of low counts (a+eps)/(b+eps)

	output:
	newenrich - the sorted list
	"""

	# get the effect size
	effects=[]
	for citem in enrich:
		if method=='bidirectional':
			lograt=np.log2((citem['observed']+epsilon)/(epsilon+citem['expected']))
			effects.append(np.abs(lograt))
		elif method=='single':
			lograt=np.log2((citem['observed'])/np.log2(citem['expected'])+epsilon)
			effects.append(lograt)
		elif method=='val':
			effects.append(citem['observed'])
		else:
			au.Debug('method %s not supported' % method)
	si=np.argsort(effects)
	newenrich=au.reorder(enrich,si[::-1])
	return newenrich


def testenrichment(data,group,method='binary',fdr=0.05,twosided=False,printit=True):
	"""
	test for enrichment for samples in groupind in the dict of arrays data
	input:
	data - a dict (by category value) of numpy arrays (each of length totseqs) of the value of each sequence
	group - the indices of the group elements
	method - the test to apply:
		'binary' - presence/abscence
		'ranksum' - not implemented yet
	fdr - the false discovery rate value or false for no fdr
	twosided - True to test both lower and higher, False to test just higher in group
	printit - True to print the significant, False to not print

	output:
	plist - a list of dict entries ('pval','observed','expected','name')
	"""

	grouplen=len(group)
	allpv=[]
	justp=[]
	for k,v in data.items():
		if method=='binary':
			gvals=v[group]
			gnz=np.count_nonzero(gvals)
			anz=np.count_nonzero(v)
			pnull=float(anz)/len(v)
			p1=stats.binom.cdf(grouplen-gnz,grouplen,1-pnull)
			if twosided:
				p2=stats.binom.cdf(gnz,grouplen,pnull)
				p=min(p1,p2)
			else:
				p=p1
			pv={}
			pv['pval']=p
			pv['observed']=gnz
			pv['expected']=pnull*grouplen
			pv['name']=k
			allpv.append(pv)
			justp.append(p)
		elif method=='ranksum':
			rdat=v
			notgroup=np.setdiff1d(np.arange(len(v)),group)
			u,p=stats.mannwhitneyu(rdat[group],rdat[notgroup])
			pv={}
			pv['pval']=p
			pv['observed']=np.mean(rdat[group])
			pv['expected']=np.mean(rdat)
			pv['name']=k
			allpv.append(pv)
			justp.append(p)
		else:
			au.Debug(9,'testenrichment method not supported',method)
			return False
	if fdr:
		fval=au.fdr(justp)
		keep=np.where(np.array(fval)<=fdr)
		keep=keep[0]
	else:
		keep=np.arange(len(justp))
	plist=[]
	rat=[]
	for cidx in keep:
		plist.append(allpv[cidx])
		rat.append(np.abs(float(allpv[cidx]['observed']-allpv[cidx]['expected']))/np.mean([allpv[cidx]['observed'],allpv[cidx]['expected']]))
	si=np.argsort(rat)
	si=si[::-1]
	if printit:
		for idx,crat in enumerate(rat):
			print(plist[si[idx]])
	return(plist)


def testbactenrichment(expdat,seqs,cdb=False,bdb=False,dbexpres=False,translatestudy=False):
	"""
	test for enrichment in bacteria database categories for the bacteria in the list seqs
	enrichment is tested against manual curation (if cdb not False) and automatic curation (if bactdb not false)

	input:
	expdat
	seqs - the sequences in the cluster
	cdb - the cooldb (manual curation) or false to skip
	bactdb - the automatic database or false to skip
	dbexpres - the assignment of values to all bacteria in the experiment (for bactdb) or false to calulate it. it is the output of bactdb.GetSeqListInfo()

	output:
	dbexpres - new if calculated
	"""

	# maybe need to keep similar freq bacteria?
	if cdb:
		cooldb.testenrichment(cdb,expdat.seqs,seqs)
	if bdb:
		if not dbexpres:
			dbexpres=bactdb.GetSeqListInfo(bdb,expdat.seqs,info='studies')
		seqpos=findseqsinexp(expdat,seqs)
		plist=testenrichment(dbexpres,seqpos,printit=False)
		for cpv in plist:
			cname=cpv['name']
			if translatestudy:
				studyname=bactdb.StudyNameFromID(bdb,cname)
			else:
				studyname=cname
			print("%s - observed %f, expected %f, pval %f" % (studyname,cpv['observed'],cpv['expected'],cpv['pval']))
	return dbexpres


def getdiffsummary(expdat,seqs,field,val1,val2=False,method='mean'):
	"""
	get the fold change between 2 groups in each of the sequences in seqs
	for zech chinese ibd paper
	input:
	expdat
	seqs - the sequences to examine
	field - name of the field dividing the 2 groups
	val1 - value of the field for group 1
	val2 - value of the field for group 2 or False for all the rest (not val1)
	method:
		- mean - calculate the difference in the mean of the 2 groups

	output:
	diff - a list of the difference between the 2 groups for each sequence
	"""

	pos1=hs.findsamples(expdat,field,val1)
	if val2:
		pos2=hs.findsamples(expdat,field,val2)
	else:
		pos2=hs.findsamples(expdat,field,val1,exclude=True)

	diff=[]
	for cseq in seqs:
		if cseq in expdat.seqdict:
			seqpos=expdat.seqdict[cseq]
		else:
			diff.append[np.nan]
			continue
		if method=='mean':
			cval1=np.mean(expdat.data[seqpos,pos1])
			cval2=np.mean(expdat.data[seqpos,pos2])
			threshold=0.1
		elif method=='binary':
			cval1=np.mean(expdat.data[seqpos,pos1]>0)
			cval2=np.mean(expdat.data[seqpos,pos2]>0)
			threshold=0.001
		else:
			au.Debug(9,"Unknown method %s for getdiff" % method)
			return False
		if cval1<=threshold and cval2<=threshold:
			diff.append(np.nan)
			continue
		if cval1<threshold:
			cval1=threshold
		if cval2<threshold:
			cval2=threshold
		cdiff=np.log2(cval1/cval2)
		diff.append(cdiff)
	return diff