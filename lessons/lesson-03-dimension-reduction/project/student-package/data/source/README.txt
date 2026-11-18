#######################################
Contact:
Cesare Furlanello <furlan@fbk.eu>
Marco Chierici <chierici@fbk.eu>
Davide Albanese <albanese@fbk.eu>

Fondazione Bruno Kessler, Trento, Italy

Last updated: November 28, 2012
#######################################

All the uploaded files follow the agreed format guidelines.


SEQC_NB_TUC_G_log2.txt.gz
-------------------------

Genes x Samples table with gene-level expression quantified by
cufflinks on RefSeq genes and reported as log2(1 + FPKM).

SEQC_NB_TUC_T_log2.txt.gz
-------------------------

Transcripts x Samples table with transcript-level expression
quantified by cufflinks on RefSeq transcripts and reported as log2(1 + FPKM).

SEQC_NB_TUC_J_log2.txt.gz
-------------------------

Junctions x Samples table with junction-level expression computed on RefSeq
junctions and reported as log2( RPM(1 + rawCount) ).

To count reads that align to known junctions, we followed the approach
recently proposed by Pervouchine DD, Knowles DG, and Guigó R. (Intron-Centric
Estimation of Alternative Splicing from RNA-seq data. Bioinformatics, nov 2012),
using the open source software bam2ssj developed by the Authors.

The junction names (provided by the software) are built on the genomic coordinates
of the introns.

SEQC_NB_TUC_J_totals.txt
------------------------

Companion file for SEQC_NB_TUC_J_log2.txt.gz, reporting the total counts of
junction-mapped reads for each sample.

