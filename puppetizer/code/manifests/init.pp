class puppetizer_main (
  Hash $gems = {},
  String $puppetdb_host = 'localhost',
  Hash $java_args = {},
  Boolean $metrics = false,
  Boolean $profiler = false,
  Boolean $external_ca = false, # TODO
  Integer $instances = 1
){
  include ::stdlib
  include ::puppetdb::params
  
  $user = 'puppet'
  
# TODO: move config to another class
# TODO: external ca
# TODO: nginx proxy from another container (?)
  
  $gems.each | $k, $v | {
    package { $k:
      provider => puppetserver_gem,
      require => Anchor['puppetserver-install'],
      * => $v
    }
  }
  
  class { ::puppetserver:
    version => '5.1.4',
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
    'jruby-puppet.max-active-instances' => $instances
  }
  
  $_java_args.each | $k, $v | {
    puppetserver::config::java_arg { $k: value   => String($v) }
  }
  
  $config = {
    'puppetserver.conf' => $_puppetserver_opts,
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
  # TODO: /etc/puppetlabs/puppetserver/services.d/ca.cfg
  
  $conf_base_dir = '/etc/puppetlabs/puppetserver'
  $conf_services_dir = "${conf_base_dir}/services.d"
  
  file {$conf_services_dir:
    ensure => directory,
    purge => true,
    recurse => true,
    backup => false,
    force => true,
    notify => Service[$::puppetserver::service]
  }->
  file { "${conf_services_dir}/ca.cfg":
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
  
  #"runuser -u ${user} -- /opt/puppetlabs/server/apps/puppetserver/bin/puppetserver reload"
  
  class { ::puppetdb::master::config:
    puppetdb_server => $puppetdb_host,
    puppetdb_disable_ssl => true,
    strict_validation => false,
    puppet_service_name => $::puppetserver::service,
    restart_puppet => $::puppetizer['running'],
    require => Anchor['puppetserver-config'],
  }
  
  anchor { 'puppetserver-install': }->
  anchor { 'puppetserver-config': }->
  anchor { 'puppetserver-run': }->
  Service[$::puppetserver::service]
  
#  package { 'json':
#    ensure   => present,
#    provider => puppetserver_gem,
#  }
  
#  class { 'r10k':
#    remote   => 'git@github.com:someuser/puppet.git',
#    provider => 'puppet_gem',
#  }
  
#  puppetizer::health { 'sleep':
#    command => '/bin/kill -0 $(cat /tmp/sleep.pid); exit $?'
#  }
}
