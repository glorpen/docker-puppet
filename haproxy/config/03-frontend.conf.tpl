frontend https-in
    mode tcp
    bind *:${port}
    # From http://byte-consult.be/2014/01/28/using-haproxy-as-an-ssl-gateway/
    # Better described here: http://blog.haproxy.com/2012/04/13/enhanced-ssl-load-balancing-with-server-name-indication-sni-tls-extension/

    option socket-stats
    tcp-request inspect-delay 5s
    tcp-request content accept if { req_ssl_hello_type 1 }

    #each-target: use_backend ${backend_name} if { req_ssl_sni -i ${hostname} }
