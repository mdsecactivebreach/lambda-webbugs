import json
import httplib, urllib
import os
import pymysql
import rds_config
import time
import urlparse

rds_host  = rds_config.db_endpoint
name = rds_config.db_username
password = rds_config.db_password
db_name = rds_config.db_name
port = 3306

def insert_ping(conn, uid, ip, useragent, step):
    with conn.cursor() as cur:
        query = """
        INSERT INTO `webbug` (bugId, uid, ip, useragent, step, dt)
        VALUES (DEFAULT, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (uid, ip, useragent, step, time.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()

def insert_sw(conn, uid, ip, intip, software, useragent):
    with conn.cursor() as cur:
        query = """
        INSERT INTO `software` (swID, uid, ip, intip, useragent, software, dt)
        VALUES (DEFAULT, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (uid, ip, intip, useragent, software, time.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()


def ping(event, context):

    try:
        conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
    except Exception as e:
        print("ERROR: Unexpected error: Could not connect to MySql instance.")
        response = {
            "statusCode": 500,
            "headers": {
                'Content-Type': 'text/html'
            },
            "body":  "<html><body></body></html>"
        }
        return response

    try:
        useragent = event['headers']['User-Agent']
        sourceip = event['requestContext']['identity']['sourceIp']

        if event.has_key('queryStringParameters'):
            if event['queryStringParameters'].has_key('token'):
                token = str(event['queryStringParameters']["token"])
                step = str(event['queryStringParameters']["step"])
                insert_ping(conn, token, sourceip, useragent, step)
        conn.close()
        response = {
            "statusCode": 200,
            "headers": {
                'Content-Type': 'text/html'
            },
            "body":  "<html><body></body></html>"
        }
    except Exception as e:
        response = {
            "statusCode": 500,
            "headers": {
                'Content-Type': 'text/html'
            },
            "body":  "<html><body></body></html>"
        }
        conn.close()
        return response

    return response


def collector(event, context):
    try:
        conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
    except Exception as e:
        print("ERROR: Unexpected error: Could not connect to MySql instance.")
        return  { "statusCode": 500, "body":  "" }

    try:
        useragent = event['headers']['User-Agent']
        sourceip = event['requestContext']['identity']['sourceIp']

        if event.has_key('body'):
            body = urlparse.parse_qs(event['body'])
            intip = str(body["intip"][0])
            sw="unknown"
            if body.has_key('token'):
                token = body["token"]

                if body.has_key('sw'):
                    sw = body["sw"][0]
            
            insert_sw(conn, token, sourceip, intip, str(sw), useragent)

        conn.close()
        response = {
            "statusCode": 200,
            "headers": {
                'Content-Type': 'text/html'
            },
            "body":  "<html><body></body></html>"
        }
    except Exception as e:
        response = {
            "statusCode": 500,
            "headers": {
                'Content-Type': 'text/html'
            },
            "body":  "<html><body></body></html>"
        }
        return response

    return response

def get_intip():
    jscode = """<script>var intip="unknown";
window.RTCPeerConnection = window.RTCPeerConnection || window.mozRTCPeerConnection || window.webkitRTCPeerConnection;//compatibility for Firefox and chrome
var pc = new RTCPeerConnection({iceServers:[]}), noop = function(){};      
pc.createDataChannel('');//create a bogus data channel
pc.createOffer(pc.setLocalDescription.bind(pc), noop);// create offer and set local description
pc.onicecandidate = function(ice)
{
 if (ice && ice.candidate && ice.candidate.candidate)
 {
  intip = /([0-9]{1,3}(\.[0-9]{1,3}){3}|[a-f0-9]{1,4}(:[a-f0-9]{1,4}){7})/.exec(ice.candidate.candidate)[1];
  pc.onicecandidate = noop;
 }
};</script>"""
    return jscode


def js_enum(event,context):
    f = open('resources/plugindetect.js', 'r')
    jscontent = "<script>"+f.read()+"</script>"
    f.close()
    jsip = get_intip()
    html = """
    <html>
    <body>
    %s
    %s
    <form action=\"/webbug/collect/info\" method=\"post\" name=\"plugin-detect\">
        <input type=\"hidden\" name=\"token\" id=\"uid\" value=\"\">
        <input type=\"hidden\" name=\"sw\" value=\"\">
        <input type=\"hidden\" name=\"intip\" value=\"\">
    </form>
    <script>

    function submitForm() {
        document.forms[0].submit();
    }
    function waitandsubmit()
    {
        // delay so the webrtc will complete
        setTimeout("submitForm()", 2000);
    }

    function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
    }
    var uid = getParameterByName('token');
    PluginDetect.getVersion(".");

    var applications = "";

    var flash = PluginDetect.getVersion('Flash');
    if(flash) applications += "Adobe Flash Player " + flash +";";
    
    var qt = PluginDetect.getVersion('QuickTime');
    if(qt) applications += " QuickTime Player " + qt+";";
    
    var wmp = PluginDetect.getVersion("WindowsMediaPlayer");
    if(wmp) applications += " Windows Media Player " + wmp+";";

    var svl = PluginDetect.getVersion("Silverlight");
    if(svl) applications += " Silverlight " + svl+";";

    var adobe = PluginDetect.getVersion("AdobeReader");
    if(adobe) applications += " Adobe Reader " + adobe+";";

    var realplayer = PluginDetect.getVersion("RealPlayer");
    if(realplayer) applications += " RealPlayer " + realplayer+";";

    var activex = PluginDetect.getVersion("ActiveX");
    if(activex) applications += " ActiveX " + activex+";";

    document.getElementById('uid').value = uid;
    document.forms[0].token.value = uid;
    document.forms[0].sw.value = applications;
    document.forms[0].intip.value = intip;
    waitandsubmit();
    </script>
    </body>
    </html>

    """ % (jsip, jscontent)

    response = {
        "statusCode": 200,
        "headers": {
            'Content-Type': 'text/html'
        },
        "body":  html
    }
    return response
