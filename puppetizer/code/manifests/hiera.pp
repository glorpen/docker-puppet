class puppetizer_main::hiera (
  Optional[Hash] $hiera_defaults = undef,
  Optional[Array] $hiera_hierarchy = undef,
){
  
  ini_setting { "puppet.conf-hiera-master":
    section => 'master',
    setting => 'hiera_config',
    path    => "${::puppetizer_main::conf_puppet_base_dir}/puppet.conf",
    value   => "${::puppetizer_main::conf_puppet_base_dir}/hiera-master.yaml",
  }
  
  $def_hiera_defaults = {"data_hash" => 'yaml_data'}
  $def_hiera_hierarchy = [
    {
      "name" => "Nodes",
      "path" => "nodes/%{trusted.certname}.yaml"
    },
    {
      "name" => "Operating System",
      "path" => "os/%{facts.os.name}.yaml"
    },
    {
      "name" => "Common defaults",
      "path" => "common.yaml"
    }
  ]
  
  
  $_hiera_defaults = merge(
    pick($hiera_defaults, $def_hiera_defaults),
    { 'datadir' => "${::puppetizer_main::conf_code_dir}/environments/%{environment}/hieradata" }
  )
  $_hiera_hierarchy = pick($hiera_hierarchy, $def_hiera_hierarchy)
  
  file { "${::puppetizer_main::conf_puppet_base_dir}/hiera-master.yaml":
    ensure => 'present',
    mode => "a=r,gu+rX,u+w",
    owner => 'root',
    group => 'root',
    content => template('puppetizer_main/hiera.yaml.erb'),
    require => Anchor['puppetserver-config'],
    notify => Service[$::puppetserver::service]
  }
}
