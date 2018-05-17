class puppetizer_main::puppetdb (
  Optional[String] $host = undef,
){
  include ::puppetdb::params
  
  if $host == undef {
    # image should be built with puppetdb support, disable it on runtime if needed
    file { "${::puppetdb::params::puppet_confdir}/routes.yaml":
      ensure => absent,
      backup => false
    }
    
    ini_setting { "puppet.conf-storeconfigs":
      setting => 'storeconfigs',
      path    => "${::puppetizer_main::conf_puppet_base_dir}/puppet.conf",
      value   => false,
      section => 'master'
    }
  } else {
    class { ::puppetdb::master::config:
      puppetdb_server => $host,
      puppetdb_disable_ssl => true,
      strict_validation => false,
      puppet_service_name => $::puppetserver::service,
      restart_puppet => $::puppetizer['running'],
      require => Anchor['puppetserver-config'],
    }
    
  }
  
}