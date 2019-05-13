# sonic Innovium ONE image installer

SONIC_ONE_IMAGE = sonic-innovium.bin
$(SONIC_ONE_IMAGE)_MACHINE = innovium
$(SONIC_ONE_IMAGE)_IMAGE_TYPE = onie
$(SONIC_ONE_IMAGE)_LAZY_INSTALLS += $(CEL_MIDSTONE_200I_PLATFORM_MODULE)
$(SONIC_ONE_IMAGE)_DOCKERS += $(DOCKER_DATABASE) \
         				      $(DOCKER_LLDP_SV2) \
         				      $(DOCKER_SNMP_SV2) \
         				      $(DOCKER_PLATFORM_MONITOR) \
         				      $(DOCKER_DHCP_RELAY)
SONIC_INSTALLERS += $(SONIC_ONE_IMAGE)
