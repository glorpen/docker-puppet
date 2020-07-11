backend ${name}
    #balance leastconn
    mode tcp

    # maximum SSL session ID length is 32 bytes.
    stick-table type binary len 32 size 30k expire 30m

    acl clienthello req_ssl_hello_type 1
    acl serverhello rep_ssl_hello_type 2

    # use tcp content accepts to detects ssl client and server hello.
    tcp-request inspect-delay 5s
    tcp-request content accept if clienthello

    # no timeout on response inspect delay by default.
    tcp-response content accept if serverhello

    stick on payload_lv(43,1) if clienthello

    # Learn on response if server hello.
    stick store-response payload_lv(43,1) if serverhello

    option ssl-hello-chk

    server ${name} ${host}:${port} resolvers dns
