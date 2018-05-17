class puppetizer_main::r10k (
  Optional[String] $repo = undef,
){
  if $repo != undef {
    package { 'json':
      ensure   => present,
      provider => puppetserver_gem,
    }
    class { 'r10k':
      remote   => $repo,
      provider => 'puppet_gem',
    }
    
    Anchor['puppetserver-config']->
    Package['json']->
    Class['r10k']
  }
}
