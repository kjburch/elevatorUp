#!/usr/bin/env bash

ASSIGNNAME="elevatorup"
EXPERS="1,1,25 2,2,25 50,16,10"
METRICS="stops maxq avgdelay stddelay"
GOLD_SEED=374837
GOLD_RUNS=500
EXAMPLE_SEEDS="646328 9 2800574"
EXAMPLE_N=3
EXAMPLE_RUNS=100
GRADE_SEED=229206
GRADE_RUNS=200
unpack_experiment()
{
	local floors=${1%,*}   #F,V
	local vators=${floors#*,}  #V
	local days=${1##*,}    #D
	floors=${floors%,*}        #F

	echo "floors=${floors}; vators=${vators}; days=${days};"
}

missingdata=0
experiment()
{
	local theSIM="${1}"
	local exper="${2}"
	local RUNS="${3}"
	local SEED="${4}"		
	local missingdata=0
	local residfmt="__residual-%s-%s-%d.%s"
	local residrand
	local residoutput

	local floors
	local vators
	local days
	eval "`unpack_experiment ${2}`"

    for ((i=0; i<${RUNS}; i++)); do 
        test $(( $i % 50 )) -eq 0 && echo -n >&2 $i " "
        residrand=`printf ${5:-${residfmt}} $exper random $i dat 2>/dev/null`
        residoutput=`printf ${5:-${residfmt}} $exper output $i log 2>/dev/null`
        eszero "${theSIM}" ${floors} ${vators} <(Random $(( SEED + i + j )) |tee "${residrand}" ) ${days} \
                | tee "${residoutput}" \
                | "${SIMGRADING}/output-pipe" | tr '\n' ' '  
        echo
    done | run_checknumeric f5+ u f5+ f5+ | awk \
            -v dat1=__stops-${exper}-$SEED-$RUNS.dat \
            -v dat2=__maxq-${exper}-$SEED-$RUNS.dat \
            -v dat3=__avgdelay-${exper}-$SEED-$RUNS.dat \
            -v dat4=__stddelay-${exper}-$SEED-$RUNS.dat \
            '{ print $1 >dat1; print $2 >dat2; print $3 >dat3; print $4>dat4 }'
	echo ${RUNS} >&2

	for m in ${METRICS} ; do 
	    test `ncdat "__${m}-${exper}-${SEED}-${RUNS}.dat"` -ne ${RUNS} && missingdata=1   
	done

	for m in ${METRICS} ; do 
		for x in _${m}-${exper}-${SEED}-${RUNS}.dat ; do
			lineswithdata "_${x}" | sort -g |${SIMGRADING}/ecdf >${x}
		done
	done


	return ${missingdata}
}


###
# SIMS and usage should be defined before sourcing sim-lib.sh
###
SIMS=elevatorup
usage()
{
	cat <<EoT
ASSIGNMENT SPECIFIC OPTIONS 

  $ /assignment/specific/path/grader.sh . [RUNS [SEED]]

Where

  . is the SIM location (required first parameter)

  RUNS is the number of RUNS to use for SIM execution and plot generation

  SEED is a positive integer for a SEED to use for random file inputs

To retain residual data files to (maybe) assist in debugging, export

  $ export GRADER_SAVE_RESIDUALS=${SIMS}

EoT
}

# if SIMGRADING is unknown
test -z "${SIMGRADING}" -a -r ~khellman/SIMGRADING/sim-lib.sh && ~khellman/SIMGRADING/setup.sh ~khellman/SIMGRADING
if ! test -r "${SIMGRADING}/sim-lib.sh" ; then
	cat >&2 <<EoT
ERROR:  SIMGRADING is not in your environment or SIMGRADING/sim-lib.sh cannot
be found.  Have you followed the grader tarball setup.sh instructions on the
assignment's Wiki page?
EoT
	exit 1
fi

test -n "${SIMGRADING}" && source "${SIMGRADING}/sim-lib.sh"

set -e

RUNS=${1:-${GRADE_RUNS}}
SEED=${2:-${GRADE_SEED}}

gradermodebackchannel 

test_nonexist_tracefile "${simloc}/SIM" 1 1 MISSINGRANDOM 1

test_truncated_tracefile "${simloc}/SIM" 10 10 TRUNCRANDOM_10 10 


test_sim_result()
{
	local exp=${1}
	local got=${2}
	local name=${3}
	local hexp=${4}
	if ! awk -v "e=${exp}" -v "g=${got}" 'BEGIN { if( e != g ) exit 1 ; else exit 0; }' ; then
		cat >&2 << EoT
invocation
  ${simloc}/SIM ${FLOORS} ${VATORS} TRACEFILE ${DAYS}
should produce output value for '${name}' of ${hexp}, SIM produced '${got}' instead.
EoT
		exit 1
	fi
	return 0
}


FLOORS=5
VATORS=500
DAYS=1
grader_msg <<EoT
Testing with FLOORS=${FLOORS} ELEVATORS=${VATORS} DAYS=${DAYS} as a consistency
check. Each person gets their own elevator (which is NOT the same as each
elevator is used exactly once...). Should result in output of 
  stops=2 maxq=0 avgdelay=0 stddelay=0 
EoT
eszero "${simloc}/SIM" ${FLOORS} ${VATORS} <("${SIMGRADING}/Random" ${SEED}) ${DAYS} | \
	"${SIMGRADING}/output-pipe" | ( tr '\n' ' '; echo ) | \
while read stops maxq avgdelay stddelay ; do
	test_sim_result       2.00000  ${stops}     STOPS        2.00000
	test_sim_result       0        ${maxq}      MAXQ         0
	avgdelay=${avgdelay/-0./0.}
	avgdelay=${avgdelay/+0./0.}
	test_sim_result       0.00000  ${avgdelay}  AVGDELAY     0.00000
	test_sim_result       0.00000  ${stddelay}  STDDELAY     0.00000 
done
grader_msg <<EoT
Consistency check FLOORS=${FLOORS} ELEVATORS=${VATORS} DAYS=${DAYS} passed.
EoT
echo



grader_msg <<EoT
Running several SIM experiments with varying FLOORS, ELEVATORS, and DAYS.  This
may take some time ...
If the test exits with a "checknumeric" error, then one of your OUTPUT values
is improperly formatted (or missing data has confused the format analysis).
EoT
set -e
missingdata=0
for S in ${EXPERS} ; do
	eval "`unpack_experiment ${S}`"
	grader_msg <<EoT
Running FLOORS=${floors} ELEVATORS=${vators} DAYS=${days}
EoT
	experiment "${simloc}/SIM" ${S} ${RUNS} ${SEED}
	missingdata=$?

    grader_msg <<EoT
... generating comparison plots for ${S} ...
EoT
    for x in ${METRICS} ; do 
		gplotpdf ${x} ${S} ${RUNS} ${SEED}
    done

	grader_cleanup_experiment ${missingdata} "${METRICS}" "${S}" "${RUNS}" "${SEED}"

    grader_save_residuals ${S}

done

grader_signoff ${RUNS} ${SEED}

