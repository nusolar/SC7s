#!/bin/bash

TAGS=(LFLA EFLA AMOT TERR RERR BCUR BVOL VVEL MVEL PHSB PHSC VIMG VREL CIMG CREL BEMQ BEMD 15VS 19VS 33VS MTMP HTMP BSPT ODMT DCBA SSPE MPIV MPIC MPOV MPOC MPMST MPCT MP12V MP3V MPMOV MPMIC MPCRXE MPTXE MPTXO MPEFLA MPLFLA MPM MPTC MPPCOV MPPCT MPSMIV MPSMIC MPCRM MPCRMOV MPCRMIC)

echo "Printing missing tags, if any..."

for tag in "${TAGS[@]}"
do
    cat $1 | grep "\'Tag\': \'${tag}\'" > /dev/null
    if (($? != 0))
    then
        echo $tag
    fi
done


