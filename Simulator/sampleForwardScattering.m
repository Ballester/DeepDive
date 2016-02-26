function forward = sampleForwardScattering(decay,maxForward)

    numvec = 100*exp(decay*(0:-0.1:-maxForward*0.1));
    randomDistVec =[];
    for i=1:50
        randomDistVec = [randomDistVec;i*ones(uint32(round(numvec(i))),1)];

    end

    forward = randsample(randomDistVec,1);
end