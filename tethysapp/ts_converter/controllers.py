from django.shortcuts import render
from utilities import *
from tethys_apps.sdk.gizmos import Button
from tethys_gizmos.gizmo_options import *
from owslib.wps import WebProcessingService
from owslib.wps import printInputOutput
from tethys_apps.sdk import get_wps_service_engine
from owslib.wps import monitorExecution
from owslib.wps import WPSExecution
from datetime import datetime
import urllib2
import urllib
import json
# -- coding: utf-8--

#Base_Url_HydroShare REST API
url_base='http://{0}.hydroshare.org/hsapi/resource/{1}/files/{2}'

##Call in Rest style
def restcall(request,branch,res_id,filename):

    print "restcall",branch,res_id,filename
    url_wml= url_base.format(branch,res_id,filename)

    response = urllib2.urlopen(url_wml)

    html = response.read()

    timeseries_plot = chartPara(html,filename)

    context = {"timeseries_plot":timeseries_plot}

    return render(request, 'ts_converter/home.html', context)

#Normal Get or Post Request
#http://dev.hydroshare.org/hsapi/resource/72b1d67d415b4d949293b1e46d02367d/files/referencetimeseries-2_23_2015-wml_2_0.wml/

def View_R_Code(request):
    r = urllib2.urlopen('http://127.0.0.1:8282/wps/R/scripts/timeSeriesConverter.R')
    r_html = r.read()
    r_code = r_html
    context = {'r_code':r_code
              }
    return render(request, 'ts_converter/View_R_Code.html', context)

def home(request):
    url_wml=None
    name = None
    show_time = False
    no_url = False
    output_converter = None
    number_ts = []#stores highcharts info of each time series
    list_ts = []#list of time series urls
    plot = None
    if request.POST and "add_ts" in request.POST:
        list_ts.append('url_name' in request.POST)
    else:
        name = "ness"

    if request.POST and "run" in request.POST:
        #plotting the unaltered time seres

        if request.POST and 'url_name' in request.POST:
               url_wml = request.POST['url_name']
               response = urllib2.urlopen(url_wml)
               html = response.read()

               graph_original = Original_Checker(html)
               number_ts2 = [{'name':"timeseries1", 'data':graph_original['for_highchart']}]
               plot = chartPara(graph_original,number_ts2)
               save_url = request.POST['url_name']#Allows URL to be saved between POST requests
        else:
            save_url = "Please enter Url"

        #saving the url between first graph and graphing the changed time series
        save1_url = save_url


        #this is the default chart if no values are given
        if url_wml is None:
            filename = 'KiWIS-WML2-Example.wml'
            url_wml='http://www.waterml2.org/KiWIS-WML2-Example.wml'
            no_url = True
            response = urllib2.urlopen(url_wml)
            html = response.read()
            graph_info = Original_Checker(html)

            number_ts1 = [{'name':"timeseries1", 'data':graph_info['for_highchart']}]
            plot = chartPara(graph_info,number_ts1)

        # Plotting the altered time series
        else:
            url_wps = 'http://localhost:8282/wps/WebProcessingService'
            url_user = url_wml
            interval = request.POST['select_interval']
            #interval = "daily"
            stat = request.POST['select_stat']
            #stat = "mean"
            #replace "=" with "!" and "&" with "|"
            #url_user = 'http://worldwater.byu.edu/app/index.php/byu_test_justin/services/cuahsi_1_1.asmx/GetValuesObject?location!byu_test_justin:B-Lw~variable!byu_test_justin:WATER~startDate!~endDate!'
            url_user = url_user.replace('=', '!')
            url_user = url_user.replace('&', '~')
            process_input = '<?xml+version="1.0"+encoding="UTF-8"+standalone="yes"?><wps:Execute+service="WPS"+version="1.0.0"++xmlns:wps="http://www.opengis.net/wps/1.0.0"+xmlns:ows="http://www.opengis.net/ows/1.1"++xmlns:xlink="http://www.w3.org/1999/xlink"+xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"++xsi:schemaLocation="http://www.opengis.net/wps/1.0.0++http://schemas.opengis.net/wps/1.0.0/wpsExecute_request.xsd">++<ows:Identifier>org.n52.wps.server.r.convert-time-series</ows:Identifier>++<wps:DataInputs>++++<wps:Input>++++++<ows:Identifier>url</ows:Identifier>++++++<wps:Data>++++++++<wps:LiteralData>'+url_user+'</wps:LiteralData>++++++</wps:Data>++++</wps:Input>++++<wps:Input>++++++<ows:Identifier>interval</ows:Identifier>++++++<wps:Data>++++++++<wps:LiteralData>'+interval+'</wps:LiteralData>++++++</wps:Data>++++</wps:Input>++++<wps:Input>++++++<ows:Identifier>stat</ows:Identifier>++++++<wps:Data>++++++++<wps:LiteralData>'+stat+'</wps:LiteralData>++++++</wps:Data>++++</wps:Input>++</wps:DataInputs>++<wps:ResponseForm>++++<wps:ResponseDocument+storeExecuteResponse="false">++++++<wps:Output+asReference="false">++++++++<ows:Identifier>output</ows:Identifier>++++++</wps:Output>++++</wps:ResponseDocument>++</wps:ResponseForm></wps:Execute>'
            wps_request = urllib2.Request(url_wps,process_input)
            wps_open = urllib2.urlopen(wps_request)
            wps_read = wps_open.read()

            graph_info =TimeSeriesConverter(wps_read)

            #testing add a fixed number of timeseries to graph
            for x in range(1,4):

                number_ts.append({'name':x,'data':graph_info['for_highchart']})
                downloading = graph_info['for_highchart']

            #number_ts = [{'name':"timeseries1", 'data':graph_original['for_highchart']},{'name':"Converted_Time_Series", 'data':graph_info['for_highchart']}]
            plot = chartPara(graph_original,number_ts)

    if request.POST and "download" in request.POST:


                name = download_csv("larry")


    text_input_options = TextInput(display_text='Enter URL of Water ML data',
                                   name='url_name',
                                   initial = "save1_url",
                                   attributes= "width: 1000")

    select_interval = SelectInput(display_text='Select a new time frame',
                            name='select_interval',
                            multiple=False,
                            options=[('Select a new interval', 'default'),('Daily', 'daily'),('Weekly','weekly'), ('Monthly', 'monthly'), ('Yearly','yearly')],
                            original=['Two'])
    select_stat = SelectInput(display_text='Select a statistics function',
                            name='select_stat',
                            multiple=False,
                            options=[('Select a statistics function', 'no_select'),('Mean', 'mean'), ('Median','median')],
                            original=['Two'])
    add_ts = Button(display_text='Add a Time Series',
                       name='add_ts',
                       submit=True)
    run = Button(display_text='Run Script',
                       name='run',
                       submit=True)
    download = Button(display_text='Download CSV',
                       name='download',
                       submit=True)


    context = {
'plot':plot,
'text_input_options':text_input_options,
'name':name,
'select_interval': select_interval,
'select_stat':select_stat,
'show_time':show_time,
'no_url':no_url,
'output_converter':output_converter,
'add_ts':add_ts,
'run':run,
'download':download

}
    
    return render(request, 'ts_converter/home.html', context)



