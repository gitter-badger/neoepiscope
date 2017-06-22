import bisect
import argparse
import bowtie_index
import sys
import math
#import pickle to unpickle ordered_exon_dict

codon_table = {"TTT":"F", "TTC":"F", "TTA":"L", "TTG":"L",
    "TCT":"S", "TCC":"S", "TCA":"S", "TCG":"S",
    "TAT":"Y", "TAC":"Y", "TAA":"Stop", "TAG":"Stop",
    "TGT":"C", "TGC":"C", "TGA":"Stop", "TGG":"W",
    "CTT":"L", "CTC":"L", "CTA":"L", "CTG":"L",
    "CCT":"P", "CCC":"P", "CCA":"P", "CCG":"P",
    "CAT":"H", "CAC":"H", "CAA":"Q", "CAG":"Q",
    "CGT":"R", "CGC":"R", "CGA":"R", "CGG":"R",
    "ATT":"I", "ATC":"I", "ATA":"I", "ATG":"M",
    "ACT":"T", "ACC":"T", "ACA":"T", "ACG":"T",
    "AAT":"N", "AAC":"N", "AAA":"K", "AAG":"K",
    "AGT":"S", "AGC":"S", "AGA":"R", "AGG":"R",
    "GTT":"V", "GTC":"V", "GTA":"V", "GTG":"V",
    "GCT":"A", "GCC":"A", "GCA":"A", "GCG":"A",
    "GAT":"D", "GAC":"D", "GAA":"E", "GAG":"E",
    "GGT":"G", "GGC":"G", "GGA":"G", "GGG":"G"}

def turn_to_aa(nucleotide_string):
    aa_string = ""
    for aa in range(len(nucleotide_string)//3):
        codon = codon_table[nucleotide_string[3*aa:3*aa+3]]
        if (codon == "Stop"):
            break
        else:
            aa_string += codon
    return aa_string

def my_print_function(kmer_list):
    print("WILD TYPE" + "\t" + "MUTANT TYPE")
    for wtmtPair in kmer_list:
        wt,mt = wtmtPair
        print(wt + "\t" + mt)
    return None


def kmer(normal_aa, mutated_aa = ""):
    if (len(mutated_aa) == 0):
        mutated_aa = normal_aa
    kmer_list = list()
    #Loop through window sizes
    for ksize in range(8, 12):
        for startIndex in range(len(mutated_aa)-ksize):
            kmer_list.append((normal_aa[startIndex:startIndex+ksize], mutated_aa[startIndex:startIndex+ksize]))
    final_list = list()
    for WT,MT in kmer_list:
        if (WT != MT):
            final_list.append((WT, MT))
    my_print_function(final_list)
    return final_list

def get_exons(transcript_id, mutation_pos, seq_length_left, 
              seq_length_right, exon_dict):
    ''' References exon_dict to get Exon Bounds for later Bowtie query.

        transcript_id: (String) Indicates the transcript the mutation
            is located on.
        mutation_pos: (int) Mutation's position on chromosome
        seq_length_left: (int) How many bases must be gathered
            to the left of the mutation
        seq_length_right: (int) How many bases must be gathered to
            the right of the mutation

        Return value: List of tuples containing starting indexes and stretch
        lengths within exon boundaries necessary to acquire the complete 
        sequence necessary for 8-11' peptide kmerization based on the position 
        of a mutation within a chromosome.
    '''

    ordered_exon_dict = exon_dict
    if transcript_id not in ordered_exon_dict:
        return []
    #Increase the seq length by 1 to account for mutation_pos collection
    seq_length_left += 1
    total_seq_length = seq_length_right + seq_length_left
    original_length_left = seq_length_left
    exon_list = ordered_exon_dict[transcript_id]
    middle_exon_index = 2*bisect.bisect(exon_list[::2], mutation_pos)-2
    #If the middle_exon_index is past the last boundary, move it to the last.
    if middle_exon_index > len(exon_list)-1:
        middle_exon_index -= 2
    nucleotide_index_list = []
    curr_left_index = middle_exon_index
    curr_right_index = middle_exon_index+1 #Exon boundary end indexes\
    #Increase by one to ensure mutation_pos is collected into boundaries.
    curr_pos_left = mutation_pos + 1
    curr_pos_right = mutation_pos #Actual number in chromosome
    #If the mutation is not on in exon bounds, return [].
    if (mutation_pos > exon_list[curr_right_index] or 
       mutation_pos < exon_list[curr_left_index]):
        return nucleotide_index_list
    count = 0
    while(len(nucleotide_index_list) == 0 or 
          sum([index[1] for index in nucleotide_index_list]) 
          < (original_length_left)):
        if curr_pos_left-exon_list[curr_left_index] >= seq_length_left:
            if curr_pos_left != mutation_pos+1:
                nucleotide_index_list.append((curr_pos_left-seq_length_left+1,
                                          seq_length_left))
            else:
                nucleotide_index_list.append((curr_pos_left-seq_length_left,
                                          seq_length_left))
            seq_length_left = 0
        else:
            nucleotide_index_list.append((exon_list[curr_left_index],
                                    curr_pos_left-exon_list[curr_left_index]))
            seq_length_left -= curr_pos_left-exon_list[curr_left_index]
            curr_pos_left = exon_list[curr_left_index-1]
            curr_left_index -= 2
            if curr_left_index < 0:
                print("Exceeded all possible exon boundaries!")
                #Changed total_seq_length for comparison in next while loop.
                total_seq_length = (original_length_left
                                      - seq_length_left
                                      + seq_length_right)
                break
    #Reverse list to get tuples in order
    nucleotide_index_list = list(reversed(nucleotide_index_list))
    while(len(nucleotide_index_list) == 0 or 
              sum([index[1] for index in nucleotide_index_list]) 
              < (total_seq_length)):
        if exon_list[curr_right_index] >= curr_pos_right + seq_length_right:
            if curr_pos_right == mutation_pos:
                nucleotide_index_list.append((curr_pos_right+1,
                                              seq_length_right))
            else:
                nucleotide_index_list.append((curr_pos_right,
                                              seq_length_right))
            seq_length_right = 0
        else:
            try:
                nucleotide_index_list.append((curr_pos_right+1,
                                              exon_list[curr_right_index]
                                              - curr_pos_right))
                seq_length_right -= exon_list[curr_right_index]-curr_pos_right
                curr_pos_right = exon_list[curr_right_index+1]
                curr_right_index += 2
            except IndexError:
                print("Exceeded all possible exon boundaries!")
                break
    return nucleotide_index_list


def get_seq(chrom, start, splice_length, ref_ind):
    chr_name = "chr" + chrom #proper
    start -= 1 #adjust for 0-based bowtie queries
    try:
        seq = ref_ind.get_stretch(chr_name, start, splice_length)
        return seq
    except Exception as e:
        #print e
        #print chr_name
        #print start
        #print splice_length
        #for key in ref_ind.recs:
        #    print(key)
        #raise
        #print("No ", chr_name, start, splice_length)
        return "No"

def make_mute_seq(orig_seq, mute_locs):
    mute_seq = ""
    for ind in range(len(orig_seq)):
        if ind in mute_locs:
            mute_seq += mute_locs[ind]
        else:
            mute_seq += orig_seq[ind]
    return mute_seq

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--vcf', type=str, required=False,
        default='-',
        help='input vcf or "-" for stdin'
    )
parser.add_argument('-x', '--bowtie-index', type=str, required=True,
        help='path to Bowtie index basename'
    )
parser.add_argument('-g', '--gtf', type=str, required=False,
        help='input gtf'
    )
args = parser.parse_args()
ref_ind = bowtie_index.BowtieIndexReference(args.bowtie_index)
my_file = open(args.gtf)# ex: open("gencode.txt").read()

exon_dict = {}
chrom_dict = {}
for line in my_file:
    if not line or line[0] == '#': continue
    tokens = line.strip().split('\t')
    if tokens[2] != "exon": continue
    read_info = tokens[8].split(';')
    version_in_id = read_info[1].find('.')
    if version_in_id == -1:
        transcript_id = read_info[1][16:]
    else:
        transcript_id = read_info[1][16:version_in_id]
    if transcript_id not in exon_dict:
        exon_dict[transcript_id] = [int(tokens[3]), int(tokens[4])]
    else:
        insert_point = 2*bisect.bisect(exon_dict[transcript_id][0::2],
                                       int(tokens[3]))
        #I'm assuming there aren't two exons that start at the same point.
        exon_dict[transcript_id] = (exon_dict[transcript_id][:insert_point] 
                                    + [int(tokens[3]), int(tokens[4])] 
                                    + exon_dict[transcript_id][insert_point:])
    if transcript_id not in chrom_dict:
        chrom_dict[transcript_id] = tokens[0]

try:
    if args.vcf == '-':
        if sys.stdin.isatty():
            raise RuntimeError('Nothing piped into this script, but input is '
                               'to be read from stdin')
        else:
            input_stream = sys.stdin
    else:
        input_stream = open(args.vcf)
        last_chrom = "None" #Will this work?
        for line in input_stream:
            if not line or line[0] == '#': continue
            vals = line.strip().split('\t')
            (chrom, pos, alt, info) = (vals[0], int(vals[1]), vals[4], vals[7]
                )
            tokens = info.strip().split('|')
            mute_type = tokens[1]
            if(mute_type != "missense_variant"): continue
            (trans_id, rel_pos) = (tokens[6], int(tokens[13]))
            pos_in_codon = (rel_pos+2)%3 #ATG --> 0,1,2
            if last_chrom == chrom and pos-last_pos <= (32-pos_in_codon):
                #Does it matter if mutations on same transcript?
                #The order of that if-statement is important! Don't change it!
                end_ind = pos+32-pos_in_codon
            else:
                if last_chrom != "None":
                    (left_side,right_side) = (last_pos-st_ind,end_ind-last_pos)
                    exon_list = get_exons(trans_id, last_pos, left_side, right_side,exon_dict)
                    if(len(exon_list) != 0):
                        wild_seq = ""
                        for exon_stretch in exon_list:
                            (seq_start, seq_length) = exon_stretch
                            wild_seq += get_seq(last_chrom, seq_start, seq_length, ref_ind)
                        mute_seq = make_mute_seq(wild_seq,mute_locs)
                        kmer(turn_to_aa(wild_seq), turn_to_aa(mute_seq))
                mute_locs = dict()
                st_ind = pos-30-pos_in_codon
                end_ind = pos+32-pos_in_codon
            mute_locs[(pos-st_ind)] = alt
            (last_pos,last_chrom) = (pos, chrom)
        #NEED TO FIX THIS!!!!!
        print("WHA________________T")
        wild_seq = get_seq(st_ind, end_ind, last_chrom, ref_ind)
        mute_seq = make_mute_seq(wild_seq,mute_locs)
        #@TODO, now pass into makeIntoAA/ kmer function
        #vars needed to be passed: st_ind, end_ind, last_chrom,
        #wild_seq, mute_seq
    #@TODO Repeated code above; need to clean/ make helper function
finally:
    if args.vcf != '-':
        input_stream.close()