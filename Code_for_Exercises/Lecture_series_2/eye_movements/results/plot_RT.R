## target == pacmen condition, search == present vs. absent

plot_conditions<-function(mean_data, se_data)
    {
    ## axes limits
    ymin=0
    ymax=6000
    xvals=c(4,8,12)
    xvals1 = xvals+.02
    xvals2 = xvals-.02

    ## plotting symbols for conditions
    surf.pch  <-24
    part.pch  <-21
    filled.pch<-22
    square.pch<-23

    plot(xvals, mean_data[2,], type='b', pch=surf.pch, , ylim=c(ymin,ymax), xlab="# items", ylab="mean reaction time[ms]", xaxp=c(4,12,2))

    for (k in c(1:4))
        {
        arrows(xvals, mean_data[k,]+se_data[k,], xvals, mean_data[k,]-se_data[k,], code=3, ang=90, len=.15)
        }

    points(xvals1, mean_data[1,], type='b', pch=part.pch,  bg='white')
    points(xvals,  mean_data[2,], type='b', pch=surf.pch,  bg='white')
    points(xvals2, mean_data[3,], type='b', pch=filled.pch,bg='white')
    points(xvals2, mean_data[4,], type='b', pch=square.pch,bg='white')
    }


observers = c('ipa', 'ipr', 'kvdb', 'sk', 'to', 'tp', 'vf')

## group data
all_data = array(0, dim=c(length(observers), 4, 3, 2), dimnames=list(obs=observers, condition=c('part', 'surf', 'filled', 'square'), nitems=c(4,8,12), target=c('absent', 'present')))

for (id in observers){
    sess    <- 4
    data    <- read.table(paste(id, '/', id, '_', sess, sep=''), header=TRUE)
    n_orig  <- dim(data)[1]
    data$correct <- as.numeric((data$button-6) == data$search)
    data    <- subset(data, correct==1)
    n_select<-dim(data)[1]
    show(paste('orig: ', n_orig, ', n_select: ', n_select, ' errors: ', 1-n_select/n_orig, sep=''))

    ## response latency
    data_mean<-tapply(data$rt, data.frame(data$target, data$nitems, data$search), mean)

    all_data[id,,,] = data_mean
    }

mean_all = apply(all_data, c(2,3,4), mean)
sd_all   = apply(all_data, c(2,3,4), sd)
se_all   = sd_all/sqrt(7)

par(mfrow=c(1,2), lwd=2, tck=.02, bty="n", cex=1.5, font.lab=3, font=3, font.axis=3, mar=c(3,3,1,0), mgp=c(1.2,0.3,0))

plot_conditions(mean_all[,,'present'], se_all[,,'present'])
plot_conditions(mean_all[,,'absent'],  se_all[,,'absent'])

# id = 'tp'
# sess = 1

for (id in observers){
    for (sess in 1:4){

        data <- read.table(paste(id, '/', id, '_', sess, sep=''), header=TRUE)
        data$correct <- as.numeric((data$button-6) == data$search)

        ## response latency
        data_mean<-tapply(data$rt, data.frame(data$target, data$nitems, data$search), mean)
        data_std <-tapply(data$rt, data.frame(data$target, data$nitems, data$search), sd)
        data_n   <-tapply(data$rt, data.frame(data$target, data$nitems, data$search), length)
        data_se  <-data_std/sqrt(data_n-1)


        ## mean frequency of errors
#         errors<-tapply(data$correct, data.frame(data$target, data$nitems, data$search), mean)
#         write.table(errors[,,2], paste(id, '/', id, '_', sess, '_errors', sep=''), row.names=c('misaligned', 'aligned', 'filled', 'no_inducer'))



        png(paste('figures/', id, '_', sess, '.png', sep=''), w=1280, h=640, res=100)
        par(mfrow=c(1,2), lwd=2, tck=.02, bty="n", cex=1.5, font.lab=3, font=3, font.axis=3, mar=c(3,3,1,0), mgp=c(1.2,0.3,0))

        plot_conditions(data_mean[,,'1'], data_se[,,'1'])
        plot_conditions(data_mean[,,'0'], data_se[,,'0'])

        legend(4, ymax, c("surface","non-surface", "filled", "filled only"), pch=c(surf.pch, part.pch, filled.pch, square.pch), bty="n")
        dev.off()
        }
    }