"""
Evaluates channelization in flow data based on the number an widths of channels
#
Written By: Matthew Stadelman
Date Written: 2016/02/26
Last Modifed: 2016/02/29
#
"""
#
from ApertureMapModelTools.__core__ import *
from .__BaseProcessor__ import BaseProcessor
#
#
class EvalChannels(BaseProcessor):
    # i
    def __init__(self,field,**kwargs):
        super().__init__(field,**kwargs)
        self.output_key = 'eval_chan'
        self.action = 'evaluate channels'
        self.arg_processors = {
            'thresh' : ArgProcessor('thresh',
                                    map_func = lambda x : float(x), 
                                    min_num_vals = 1,
                                    out_type = 'single' ,
                                    expected = '##',
                                    err_desc_str='to be a numeric value'),
            'dir' :  ArgProcessor('dir',
                                  map_func = lambda x : x,
                                  min_num_vals = 1,
                                  out_type = 'single' ,
                                  expected = 'str',
                                  err_desc_str='value is either x or z')    
        }
    #
    def process_data(self,**kwargs):
        r"""
        Examines the dataset along one axis to determine the number and 
        width of channels.
        """
        #
        direction = self.args['dir']
        min_val = self.args['thresh']
        #
        if (direction.lower() == 'x'):
          span = self.nx
          step = self.nz
        elif (direction.lower() == 'z'):
          span = self.nz
          step = self.nx
        else:
            print("error - invalid direction supplied, can only be x or z")
            return
        #
        self.processed_data = dict()
        channels = []
        num_channels = []
        channel_widths = []
        avg_channel_width = []
        st = 0
        for i in range(span):
            channels.append([])
            channel_widths.append([])
            bounds = [-1,-1]
            en = st + step
            for j in range(st,en,1):
                if (self.data_map[j] > min_val):
                    bounds[0] = (j if bounds[0] < 0 else bounds[0])
                else:
                    if (bounds[0] > 0):
                        bounds[1] = j-1
                        # adding to channel list and then resetting bounds
                        channels[i].append((bounds[0],bounds[1]))
                        channel_widths[i].append(bounds[1] - bounds[0] + 1)
                        bounds = [-1,-1]
            # adding end point if channel butts up against edge of fracture
            if (bounds[0] > 0):
                bounds[1] = j
                # adding to channel list and then resetting bounds
                channels[i].append((bounds[0],bounds[1]))
                bounds = [-1,-1]
            # calculating average channel width
            avg = 0
            for chan in channel_widths[i]:
                avg += chan
            n = len(channel_widths[i]) if len(channel_widths[i]) > 0 else 1.0
            avg = avg / n
            num_channels.append(len(channels[i]))
            avg_channel_width.append(avg)
            st = en
        #
        # putting data into storage dict
        self.processed_data['chan_indicies_per_row'] = channels
        self.processed_data['chans_per_row'] = num_channels
        self.processed_data['chan_widths_per_row'] = channel_widths
        self.processed_data['avg_chan_width_per_row'] = avg_channel_width        
    #
    def output_data(self,filename=None,delim = ',',**kwargs):
        r"""
        creates the output content for channelization
        """
        #
        if filename is None:
            filename = self.infile
        #
        # getting index before the extension
        ldot = filename.rfind('.')
        #
        # naming ouput file
        self.outfile_name = filename[:ldot]+'-channel_data'+filename[ldot:]
        #
        # outputting data
        content = 'Channelization data from file: '+self.infile+'\n'
        content += (self.args['dir']+'-index'+delim+'Number of Channels'+
                   delim+'Average Width'+delim+'Channel Widths\n')
        #
        num_channels = list(self.processed_data['chans_per_row'])
        avg_width = list(self.processed_data['avg_chan_width_per_row'])
        widths = list(self.processed_data['chan_widths_per_row'])
        for i in range(len(num_channels)):
            chans = [str(x) for x in widths[i]]
            chans = '('+','.join(chans)+')'
            row = '{0:4d}'+delim+'{1:3d}'+delim+'{2:0.3}'+delim+'{3}'
            row =  row.format(i,num_channels[i],avg_width[i],chans)
            content += row+'\n'
        content += '\n'
        #
        self.outfile_content = content
