class puppetizer_main (
  Hash $gems = {},
  Optional[String] $puppetdb_host = undef,
  Hash $java_args = {},
  Boolean $metrics = false,
  Boolean $profiler = false,
  Boolean $external_ca = false,
  Boolean $external_ssl_termination = false,
  Integer $max_instances = 1,
  Optional[String] $r10k_repo = undef,
  String $certname = 'puppet'
){
  include ::stdlib
  include ::puppetdb::params
  
  $user = 'puppet'
  $version = '5.3.1'
  
# TODO: https://puppet.com/docs/puppetserver/5.0/external_ssl_termination.html
# TODO: vault?
  
  $gems.each | $k, $v | {
    package { $k:
      provider => puppetserver_gem,
      require => Anchor['puppetserver-install'],
      * => $v
    }
  }
  
  class { ::puppetserver:
    version => $version,
    start => $::puppetizer['running']
  }
  
  Package[$::puppetserver::package]->
  Anchor['puppetserver-install']
  
  $_java_args = merge({
    '-Xmx' => '256m',
    '-Xms' => '128m'
  },$java_args)
  
  $_puppetserver_opts = {
    'http-client.metrics-enabled' => $metrics,
    'profiler.enabled' => $profiler,
    'jruby-puppet.use-legacy-auth-conf' => false,
    'jruby-puppet.max-active-instances' => $max_instances
  }
  
  $_java_args.each | $k, $v | {
    puppetserver::config::java_arg { $k: value   => String($v) }
  }
  
  $conf_puppet_base_dir = '/etc/puppetlabs/puppet'
  $conf_base_dir = '/etc/puppetlabs/puppetserver'
  $conf_services_dir = "${conf_base_dir}/services.d"
  
  $config = {
    'puppetserver.conf' => $_puppetserver_opts,
    # https://puppet.com/docs/puppetserver/5.0/external_ca_configuration.html
    'webserver.conf' => {
      'webserver.ssl-cert' => "${conf_puppet_base_dir}/ssl/certs/${certname}.pem",
      'webserver.ssl-key' => "${conf_puppet_base_dir}/ssl/private_keys/${certname}.pem",
      'webserver.ssl-ca-cert' => "${conf_puppet_base_dir}/ssl/certs/ca.pem",
      #'webserver.ssl-cert-chain' => "${conf_puppet_base_dir}/ssl/certs/ca-chain.pem",
      #'ssl-crl-path : /etc/puppetlabs/puppet/ssl/crl.pem
    }
  }
  
  $config.each | $target, $conf | {
    $conf.each | $k, $v | {
      $path = $k.regsubst('\.','/', 'G')
      puppetserver::config::puppetserver { "${target}/${path}":
        ensure => $v?{
          undef => 'absent',
          default => 'present'
        },
        value => String($v),
        notify => Service[$::puppetserver::service]
      }
    }
  }
  
  file {$conf_services_dir:
    ensure => directory,
    purge => true,
    recurse => true,
    backup => false,
    force => true,
    notify => Service[$::puppetserver::service]
  }->
  file { "${conf_services_dir}/ca.cfg": #conditional disable internal ca
    ensure => present,
    content => epp('puppetizer_main/services/ca.cfg.epp', {'ca'=>!$external_ca}),
    notify => Service[$::puppetserver::service]
  }
  
  
  Service <| title == $::puppetserver::service |> {
    start => "runuser -u ${user} -- /opt/puppetlabs/server/apps/puppetserver/bin/puppetserver start",
    stop => "runuser -u ${user} -- /opt/puppetlabs/server/apps/puppetserver/bin/puppetserver stop",
    status => 'kill -0 $(cat /var/run/puppetlabs/puppetserver/puppetserver.pid)',
    provider => 'base',
  }
  
  ini_setting { "puppet.conf-certname":
    section => 'master',
    setting => 'certname',
    path    => '/etc/puppetlabs/puppet/puppet.conf',
    value   => $certname
  }
  
  if $puppetdb_host == undef {
    # image should be built with puppetdb support, disable it on runtime if needed
    file { "${::puppetdb::params::puppet_confdir}/routes.yaml":
      ensure => absent,
      backup => false
    }
    
    ini_setting { "puppet.conf-storeconfigs":
      setting => 'storeconfigs',
      path    => '/etc/puppetlabs/puppet/puppet.conf',
      value   => false,
      section => 'master'
    }
  } else {
    class { ::puppetdb::master::config:
      puppetdb_server => $puppetdb_host,
      puppetdb_disable_ssl => true,
      strict_validation => false,
      puppet_service_name => $::puppetserver::service,
      restart_puppet => $::puppetizer['running'],
      require => Anchor['puppetserver-config'],
    }
    
  }
  
  anchor { 'puppetserver-install': }->
  anchor { 'puppetserver-config': }->
  anchor { 'puppetserver-run': }->
  Service[$::puppetserver::service]
  
  if $r10k_repo {
    package { 'json':
      ensure   => present,
      provider => puppetserver_gem,
    }
    
    class { 'r10k':
      remote   => $r10k_repo,
      provider => 'puppet_gem',
    }
  }
  
#  puppetizer::health { 'sleep':
#    command => '/bin/kill -0 $(cat /tmp/sleep.pid); exit $?'
#  }

}
