include $(PLATFORM_PATH)/platform-modules-cel.mk
include $(PLATFORM_PATH)/one-image.mk

SONIC_ALL += $(SONIC_ONE_IMAGE) $(DOCKER_PTF)
