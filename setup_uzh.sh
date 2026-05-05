DIR="$( dirname -- "${BASH_SOURCE[0]}"; )";
DIR="$( realpath -e -- "$DIR"; )";

source /app/cern/root_v6.32.10/bin/thisroot.sh
alias python="python3.11"
export PATH=$DIR/Combine/build/bin:$PATH
export LD_LIBRARY_PATH=$DIR/Combine/build/lib:$LD_LIBRARY_PATH
export PYTHONPATH=$DIR/Combine/build/python:$PYTHONPATH


if [[ " $@ " =~ " clean " ]]; then
    rm -rf $DIR/Combine
fi

if [[ " $@ " =~ " build " ]]; then
    git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git Combine
    cd Combine
    git checkout v10.6.0
    sed -i "s|find_package(Boost CONFIG REQUIRED COMPONENTS program_options filesystem)|find_package(Boost REQUIRED COMPONENTS program_options filesystem)|g" CMakeLists.txt
    mkdir build
    cd build
    cmake .. -DUSE_VDT=FALSE
    cmake --build . -j8
    cd ../..
    sed -i "s|/usr/bin/env python3|/usr/bin/python3.11|g" $DIR/Combine/build/bin/*.py
    python3.11 -m pip install pandas
fi
