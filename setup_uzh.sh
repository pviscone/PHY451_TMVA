DIR="$( dirname -- "${BASH_SOURCE[0]}"; )";
DIR="$( realpath -e -- "$DIR"; )";

#source /app/cern/root_v6.32.10/bin/thisroot.sh

#add micromamba (from pviscone local) and combine binary and lib (fallback on pviscone)
export PATH=/home/uzh/pvisco/.local/bin:$HOME/Combine/build/bin:/home/uzh/pvisco/Combine/build/bin:$PATH
export LD_LIBRARY_PATH=$HOME/Combine/build/lib:/home/uzh/pvisco/Combine/build/lib:$LD_LIBRARY_PATH
export PYTHONPATH=$HOME/Combine/build/python:/home/uzh/pvisco/Combine/build/python:$PYTHONPATH

alias python="python3.12"

#micromamba create -n combine python=3.12 root=6.34 gsl boost-cpp vdt eigen tbb cmake ninja pandas
eval "$(micromamba shell hook --shell bash)"
micromamba activate /home/uzh/pvisco/.local/share/mamba/envs/combine

if [[ " $@ " =~ " clean " ]]; then
    rm -rf $HOME/Combine
fi

if [[ " $@ " =~ " combine " ]]; then
    git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git $HOME/Combine
    cd $HOME/Combine
    git checkout v10.6.0

    mkdir build
    cd build
    cmake .. -DUSE_VDT=FALSE -DBOOST_ROOT=/home/uzh/pvisco/boost-1.86.0/build \
          -DBoost_DIR=/home/uzh/pvisco/boost-1.86.0/build/lib/cmake/Boost-1.86.0 \
          -DCMAKE_PREFIX_PATH=/home/uzh/pvisco/boost-1.86.0/build
    cmake --build . -j8 
    cd $DIR
fi

if [[ " $@ " =~ " combine_conda " ]]; then
    git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git $HOME/Combine
    cd $HOME/Combine
    git checkout v10.6.0

    mkdir build
    cd build
    cmake .. -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX -DCMAKE_INSTALL_PYTHONDIR=lib/python3.12/site-packages -DUSE_VDT=OFF
    cmake --build . -j8 
    cd $DIR
fi
