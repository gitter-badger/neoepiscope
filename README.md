neoepiscope [![Build Status](https://travis-ci.org/pdxgx/neoepiscope.svg?branch=master)](https://travis-ci.org/pdxgx/neoepiscope)
-----
`neoepiscope` is software for predicting neoepitopes from DNA sequencing (DNA-seq) data. Where most neoepitope prediction software confines attention to neoepitopes arising from at most one somatic mutation, often just an SNV, `neoepiscope` uses assembled haplotype output of [HapCUT2](https://github.com/vibansal/HapCUT2) to also enumerate neoepitopes arising from more than one somatic mutation. `neoepiscope` also takes into account frameshifting from indels and permits personalizing the reference transcriptome using germline variants.

License
-----
`neoepiscope` is licensed under the [MIT](http://choosealicense.com/licenses/mit/) license. See [`LICENSE`](LICENSE) for more details.

Portions of neoepiscope---specifically, segments of code in [`transcript.py`](neoepiscope/transcript.py), [`bowtie_index.py`](neoepiscope/bowtie_index.py), and [`download.py`](neoepiscope/download.py)---are taken from Rail-RNA, which is copyright (c) 2015 Abhinav Nellore, Leonardo Collado-Torres, Andrew Jaffe, James Morton, Jacob Pritt, José Alquicira-Hernández, Christopher Wilks, Jeffrey T. Leek, and Ben Langmead and licensed under the MIT License.

Installing neoepiscope
-----

First clone this repo to `/path/to/neoepiscope/repo`; then run

```pip install neoepiscope```.

To download compatible reference annotation files (hg19 and/or GRCh38) and link installations of relevant optional softwares to `neoepiscope` (e.g. netMHCpan), you will need to use our download functionality. From within `/path/to/neoepiscope/repo` run

```neoepiscope download```

and respond to the prompts as relevant for your needs. 

To make sure that the software is running properly, test it by running

```neoepiscope test```

Using neoepiscope
-----

##### Preparing reference files (for those using references other than hg19 or GRCh38)

If you aren't using hg19 or GRCh38 reference builds from our download functionality, you will need to download and prepare your own annotation files. Before calling any neoepitopes, run neoepiscope in ```index``` mode to prepare dictionaries of transcript data used in neoepitope prediction:

```neoepiscope index -g <GTF> -d <DIRECTORY TO HOLD PICKLED DICTIONARIES>```

Options:

```-g, --gtf```     path to GTF file

```-d, --dicts```   path to write pickled dictionaries

##### Ensure proper ordering of VCF

To call neoepitopes from somatic mutations, ensure that data for the tumor sample in your VCF file precedes data from a matched normal sample. If it DOES NOT, run neoepiscope in ```swap``` mode to produce a new VCF:

```neoepiscope swap -i <INPUT VCF> -o <SWAPPED VCF>```

Options:

```-i, --input```   path to input VCF

```-o, --output```  path to swapped VCF

##### Add germline variation (optional)

If you would like to include germline variation in your neoepitope prediction, ```merge``` your somatic and germline VCFs for a sample prior to running HapCUT2:

```neoepiscope merge -g <GERMLINE VCF> -s <SOMATIC VCF> -o <MERGED VCF>```

Options:

```-g, --germline```  path to germline VCF

```-s, --somatic```   path to somatic VCF

```-o, --output```    path to write merged VCF

##### Predict haplotype phasing

Next, [run HapCUT2](https://github.com/vibansal/HapCUT2#to-run) with your merged or somatic VCF (make sure to use ```--indels 1``` when running `extractHAIRS` if you wish to predict neoepitopes resulting from insertions and deletions). Before calling neoepitopes, ```prep``` your HapCUT2 output to included unphased mutations as their own haplotypes:

```neoepiscope prep -v <VCF> -c <HAPCUT2 OUTPUT> -o <ADJUSTED HAPCUT OUTPUT>```

Options:

```-v, --vcf```               path to VCF file used to generate HapCUT2 output

```-c, --hapcut2-output```    path to original HapCUT2 output

```-o, --output```            path to output file

##### Neoepitope prediction

Finally, ```call``` neoepitopes:

```neoepiscope call -b <GENOME BUILD> -c <PREPPED HAPCUT2 OUTPUT> [options]```

Options:

```-x, --bowtie-index```              path to bowtie index of reference genome

```-d, --dicts```                     path to directory containing pickled dictionaries generated in ```index``` mode

```-b, --build```                     which genome build to use (hg19 or GRCh38; overrides `-x` and `-d` options)

```-c, --merged-hapcut2-output```     path to HapCUT2 output adjusted by ```neoepiscope prep```

```-v, --vcf```                       path to VCF file used to generate HapCUT2 output

```-o, --output```		              path to output file

```-f, --fasta```					  output additional fasta file output 

```-k, --kmer-size```                 kmer size for neoepitope prediction (default 8-11 amino acids)

```-p, --affinity-predictor```        software to use for MHC binding predictions (default MHCflurry v1 with rank and affinity scores)

```-a, --alleles```                   alleles to use for MHC binding predictions

```-n, --no-affinity```               do not run binding affinity predictions, overrides the `-p` and `-a` options

```-g, --germline```                  how to handle germline mutations (by default includes as background variation)

```-s, --somatic```                   how to handle somatic mutations (by default includes for neoepitope enumeration)

```-u, --upstream-atgs```             handling of translation from upstream start codons - ("novel" (default) only, "all", "none", "reference" only)

```-i, --isolate```                   isolate mutations - disables phasing of mutations which share a haplotype

```--nmd```                           enumerate neoepitopes from nonsense mediated decay transcripts

```--pp```                            enumerate neoepitopes from polymorphic pseudogene transcripts

```--igv```                           enumerate neoepitopes from IG V transcripts

```--trv```                           enumerate neoepitopes from TR V transcripts

```--allow-nonstart```                enumerate neoepitopes from transcripts without annotated start codons

```--allow-nonstop```                 enumerate neoepitopes from transcripts without annotated stop codons

Using the `--build` option requires use of our download functionality to procure and index the required reference files for hg19 and/or GRCh38. If using an alternate genome build, you will need to download your own bowtie index and GTF files for that build and use the `neoepiscope index` mode to prepare them for use with the `--dicts` and `--bowtie-index` options.

Haplotype information should be included using ```-c /path/to/haplotype/file```. This in the form of HapCUT2 output, generated either from your somatic VCF or a merged germline/somatic VCF made with our ```neoepiscope merge``` functionality. The HapCUT2 output should be adjusted using our ```neoepiscope prep``` functionality to ensure that mutations that lack phasing data are still included in analysis.

If you wish to extract variant allele frequency information from your VCF to be output with relevant epitopes, include the path to the VCF you used to create your haplotype information using ```-v /path/to/VCF```.

To specify the output file, use ```-o /path/to/output_file```. If no output file is specified, the output will be written to standard out. By default, only data on neoepitopes is output in the file. By using the `--fasta` option, an additional file, /path/to/output_file.fasta, will be made. This is a FASTA file specifying the full-protein sequences from each mutation-affected transcript. The header in the FASTA will give the name of the transcript from which the protein originated, followed by "v[#]" for every version of the transcript. This option is only available when writing output to a file, not standard out.

The default kmer size for neoepitope enumeration is 8-11 amino acids, but a custom range can be specified using the ```--kmer-size``` argument with the minimum and maximum epitope size separated by commas (e.g. ```--kmer-size 8,20``` to get epitopes ranging from 8 to 20 amino acids in length).

For affinity prediction, `neoepiscope` currently supports predictions from `MHCflurry` [v1](https://github.com/openvax/mhcflurry), `MHCnuggets` [v2](https://github.com/KarchinLab/mhcnuggets-2.0), `netMHCpan` version [v3](http://www.cbs.dtu.dk/cgi-bin/sw_request?netMHCpan+3.0) or [v4](http://www.cbs.dtu.dk/cgi-bin/nph-sw_request?netMHCpan), and `netMHCIIpan` [v3](http://www.cbs.dtu.dk/cgi-bin/nph-sw_request?netMHCIIpan). When installing our software with `pip`, `MHCflurry` and `MHCnuggets` are automatically installed or updated. Optional integration of `netMHCpan` or `netMHCIIpan` must be done from your own installation of these softwares using our download functionality (see "Installing neoepiscope" above). 

The default affinity prediction software for `neoepiscope` is `MHCflurry` v1. To specify a custom suite of binding prediction softwares, use the `-p` argument for each software followed by its name, version, and desired scoring output(s) (e.g. ```-p mhcflurry 1 affinity,rank -p mhcnuggets 2 affinity```). To forgo binding affinity predictions, use the `--no-affinity` command line option.

Germline and somatic mutations can be handled in a variety of ways. They can be excluded entirely (e.g. ```--germline exclude```), included as background variation to personalize the reference transcriptome (e.g. ```--germline background```), or included as variants from which to enumerate neoepitopes (e.g. ```--somatic include```). The default value for `--germline` is `background`, and the default value for `--somatic` is `include`.

The choice of start codon for a transcript can also be handled with flexibility. By default, the value for the `--upstream-atgs` argument is `none`, which specifies preferential use of the reference start codon for a transcript, or alternatively the nearest ATG downstream of it in the case of a disrupted reference start codon. Alternatively, the use of ```--upstream-atgs novel``` allows for the use of a novel ATG upstream of the reference start codon in the case of a disrupted start codon. A less conservative ```--upstream-atgs all``` uses the most upstream ATG, regardless of its novelty. For a conservative option, ```--upstream-atgs reference``` requires use of only the reference start codon, preventing enumeration of neoepitopes from a transcript if the reference start codon is disrupted.

By default, `neoepiscope` only enumerates neoepitopes from protein coding transcripts with annotated start and stop codons. However, by specifying the `--nmd`, `--pp`, `--igv`, and/or `--trv` flags, you can additionally enumerate neoepitopes from nonsense mediated decay transcripts, polymorphic pseudogene transcripts, immunoglobulin variable transcripts, and/or T cell receptor variable transcripts, respectively. For further flexibility, you can add the `--allow-nonstart` and/or `--allow-nonstop` to enumerate neoepitopes from transcripts without annotated start and/or stop codons, respectively.
