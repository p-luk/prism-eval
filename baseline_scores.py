#!/usr/bin/env python

import sys
import argparse
import os
import json
import prism
from scipy import stats
import matplotlib.pyplot as plt
import pandas as pd
import statistics
import csv
import seaborn as sns

def create_arg_parser():
    """Creates and returns the ArgumentParser object."""

    parser = argparse.ArgumentParser(description='Description of your app.')
    parser.add_argument('-d','--datadir', type=str, help='Path to data from baseline_preprocess.py.')
    parser.add_argument('-o','--outputdir', type=str, help='Path to output to write scores.')
    parser.add_argument('-p','--plotdir', type=str, help='Path to output to write plots.')
    parser.add_argument('-m', '--heatmapdir', type=str, help='Path to output to write heatmap of human annotations.')
    return parser

def get_scores(datadir, outputdir):
    """
    Uses PRISM to score examples read from datadir. See README.md for proper data format
    
    Keyword arguments:
    datadir -- string directory to fetch data (tsv)
    outputdir -- string directory path to save output
    """
    prism_model = prism.Prism(model_dir=os.environ['MODEL_DIR'], lang='en')
    scores = []
    with open(datadir, 'r') as f:
        data = csv.reader(f, delimiter="\t", quotechar='"')
        header = next(data)
        header.append('prism_score')
        scores.append(header)
        ind = {'ref':(header.index('ref')), 'cand':(header.index('cand')), 'understandable':(header.index('understandable'))}
        for row in data:
            ref = row[ind['ref']]
            cand = row[ind['cand']]
            prism_score = prism_model.score(cand=[cand], ref=[ref])
            scores.append(row + [str(prism_score)])
    with open(outputdir, 'w') as f:
        dw = csv.writer(f, delimiter='\t')
        dw.writerows(scores)
    return pd.DataFrame(scores[1:],columns=scores[0])

def median_annotation(x):
    """Returns median value from list. Applied to Series."""
    return statistics.median(json.loads(x))

def plot_correlation(scores, plotdir, heatmapdir):
    """
    plots correlation between human annotation and PRISM scores
    
    Keyword arguments:
    scores -- list of examples and scores
    plotdir -- string directory path to save plots
    heatmapdir -- string directory path to save plots
    """
    prism_scores = scores['prism_score'].astype(float)
    human_annotations = ['understandable', 'natural', 'maintains_context', 'engaging','uses_knowledge','overall']
    median_annotations = pd.DataFrame()

    # construct correlation plot
    plt.figure()
    fig, ax = plt.subplots(2,3, figsize=(12,8))
    ax = ax.flatten()
    for i,quality in enumerate(human_annotations):
        # compute correlation
        quality_scores = scores[quality].apply(median_annotation).astype(float)
        median_annotations[quality] = quality_scores
        slope, intercept, r_value, p_value, std_err = stats.linregress(quality_scores, prism_scores)
        # plot
        ax[i].plot(quality_scores, prism_scores, 'o', label='original data')
        ax[i].plot(quality_scores, intercept + slope*quality_scores, 'r', label='fitted line')
        ax[i].set_title(label='{0}: $R^2=${1}\n p={2}'.format(quality, str(round(r_value**2,6)), str(round(p_value,6))))
    handles, labels = ax[i].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper right')
    fig.text(0.5, 0.00, 'Median Human Annotator Score', ha='center', fontsize=12)
    fig.text(0.02, 0.5, 'PRISM Score', va='center', rotation='vertical', fontsize=12)
    plt.suptitle('PRISM vs. Median Human Annotator Score Correlation', y=1.05)
    fig.tight_layout()

    plt.savefig(plotdir)
    plt.close()
    
    # construct heatmap
    plt.figure()
    ax = sns.heatmap(median_annotations.corr(), annot=True)
    bottom, top = ax.get_ylim()
    ax.set_ylim(bottom + 0.5, top - 0.5)
    plt.title('Median Human Quality Score Correlation')
    plt.savefig(heatmapdir)
    plt.close()

def main():
    print("Entered main ... ")
    arg_parser = create_arg_parser()
    try:
        options = arg_parser.parse_args()
    except ArgumentError():
        print('baseline_scores.py -d <datadir> -o <outputdir> -p <plotdir> -h <heatmapdir>')
    print(options)
    print('Getting scores ... ')
    scores = get_scores(datadir=options.datadir, outputdir=options.outputdir)
    print('Getting correlations...')
    plot_correlation(scores=scores, plotdir=options.plotdir, heatmapdir=options.heatmapdir)

if __name__ == '__main__':
    main()
    sys.exit(0)
