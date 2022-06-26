"""
A class to transform serialized VirtualMachineConfigInfo(vim.vm.ConfigInfo)
into VirtualMachineConfigSpec(vim.vm.ConfigSpec)
"""
from pyVmomi import vim


class VmConfigInfoToSpec(object):

    def __init__(self, config_info):
        self.config_info = config_info

    def transform(self):
        config_spec = vim.vm.ConfigSpec()

        # TODO: remove this later
        # Note: Access to properties by their name as string seems to be impossible, this doesn't work:
        # for config_property in config_info:
        #     print("%s: %s" % (config_property, type(config_info[config_property])))
        #     if isinstance(config_info[config_property], (str, int, float, bool)):
        #        # TypeError: 'vim.vm.ConfigSpec' object does not support item assignment:
        #        cspec[config_property] = config_info[config_property]
        #        # This doesn't work neiter:
        #        setattr(cspec, config_property, config_info[config_property])

        config_spec.alternateGuestName = self.config_info["alternateGuestName"]
        config_spec.annotation = self.config_info["annotation"]
        config_spec.bootOptions = self._transform_bootOptions()
        config_spec.changeTrackingEnabled = self.config_info["changeTrackingEnabled"]
        config_spec.cpuAffinity = self._transform_cpuAffinity()
        config_spec.cpuAllocation = self._transform_ResourceAllocationInfo("cpuAllocation")
        config_spec.cpuFeatureMask = self._transform_cpuFeatureMask()
        config_spec.cpuHotAddEnabled = self.config_info["cpuHotAddEnabled"]
        config_spec.cpuHotRemoveEnabled = self.config_info["cpuHotRemoveEnabled"]
        config_spec.deviceChange = self._transform_devices()
        config_spec.extraConfig = self._transform_extraConfig()
        config_spec.files = self._transform_files()
        config_spec.firmware = self.config_info["firmware"]
        config_spec.flags = self._transform_flags()
        config_spec.ftEncryptionMode = self.config_info["ftEncryptionMode"]
        config_spec.ftInfo = self._transform_ftInfo()
        config_spec.guestAutoLockEnabled = self.config_info["guestAutoLockEnabled"]
        config_spec.guestId = self.config_info["guestId"]
        config_spec.guestMonitoringModeInfo = self._transform_guestMonitoringModeInfo()
        config_spec.latencySensitivity = self._transform_latencySensitivity(self.config_info["latencySensitivity"])
        config_spec.managedBy = self._transform_managedBy()
        config_spec.maxMksConnections = self.config_info["maxMksConnections"]
        config_spec.memoryAllocation = self._transform_ResourceAllocationInfo("memoryAllocation")
        config_spec.memoryHotAddEnabled = self.config_info["memoryHotAddEnabled"]
        config_spec.memoryMB = self.config_info["hardware"]["memoryMB"]
        config_spec.memoryReservationLockedToMax = self.config_info["memoryReservationLockedToMax"]
        config_spec.messageBusTunnelEnabled = self.config_info["messageBusTunnelEnabled"]
        config_spec.migrateEncryption = self.config_info["migrateEncryption"]
        config_spec.name = self.config_info["name"]
        config_spec.nestedHVEnabled = self.config_info["nestedHVEnabled"]
        config_spec.numCoresPerSocket = self.config_info["hardware"]["numCoresPerSocket"]
        config_spec.numCPUs = self.config_info["hardware"]["numCPU"]
        config_spec.pmem = self._transform_pmem()
        config_spec.pmemFailoverEnabled = self.config_info["pmemFailoverEnabled"]
        config_spec.powerOpInfo = self._transform_defaultPowerOps()
        # Since vSphere API 7.0.1.0:
        if "sevEnabled" in self.config_info:
            config_spec.sevEnabled = self.config_info["sevEnabled"]
        # Since vSphere API 7.0:
        if "sgxInfo" in self.config_info:
            config_spec.sgxInfo = self._transform_sgxInfo()
        config_spec.swapPlacement = self.config_info["swapPlacement"]
        config_spec.tools = self._transform_tools()
        config_spec.uuid = self.config_info["uuid"]
        config_spec.vAppConfig = self._transform_vAppConfig()
        config_spec.vAssertsEnabled = self.config_info["vAssertsEnabled"]
        # Since vSphere API 7.0:
        if "vcpuConfig" in self.config_info:
            config_spec.vcpuConfig = self._transform_VirtualMachineVcpuConfig()
        config_spec.version = self.config_info["version"]
        config_spec.virtualICH7MPresent = self.config_info["hardware"]["virtualICH7MPresent"]
        config_spec.virtualSMCPresent = self.config_info["hardware"]["virtualSMCPresent"]
        config_spec.vmOpNotificationToAppEnabled = self.config_info["vmOpNotificationToAppEnabled"]

        return config_spec

    def _transform_bootOptions(self):
        config_info_boot_options = self.config_info["bootOptions"]
        boot_options = vim.vm.BootOptions()
        boot_options.bootRetryDelay = config_info_boot_options["bootRetryDelay"]
        boot_options.bootRetryEnabled = config_info_boot_options["bootRetryEnabled"]
        boot_options.efiSecureBootEnabled = config_info_boot_options["efiSecureBootEnabled"]
        boot_options.enterBIOSSetup = config_info_boot_options["enterBIOSSetup"]
        boot_options.networkBootProtocol = config_info_boot_options["networkBootProtocol"]
        for boot_order in config_info_boot_options["bootOrder"]:
            boot_device = None
            if boot_order["_vimtype"] == "vim.vm.BootOptions.BootableCdromDevice":
                boot_device = vim.vm.BootOptions.BootableCdromDevice()
            elif boot_order["_vimtype"] == "vim.vm.BootOptions.BootableDiskDevice":
                boot_device = vim.vm.BootOptions.BootableDiskDevice()
                # TODO: check if device keys can be restored as backed up
                boot_device.deviceKey = boot_order["deviceKey"]
            elif boot_order["_vimtype"] == "vim.vm.BootOptions.BootableEthernetDevice":
                boot_device = vim.vm.BootOptions.BootableEthernetDevice()
                # TODO: check if device keys can be restored as backed up
                boot_device.deviceKey = boot_order["deviceKey"]
            elif boot_order["_vimtype"] == "vim.vm.BootOptions.BootableFloppyDevice":
                boot_device = vim.vm.BootOptions.BootableFloppyDevice()

            boot_options.bootOrder.append(boot_device)

        return boot_options

    def _transform_cpuAffinity(self):
        if not self.config_info["cpuAffinity"]:
            return None
        cpu_affinity = vim.vm.AffinityInfo()
        for node_nr in self.config_info["cpuAffinity"]["affinitySet"]:
            cpu_affinity.affinitySet.append(node_nr)

        return cpu_affinity

    def _transform_cpuAllocation(self):
        if not self.config_info["cpuAllocation"]:
            return None

        return self._transform_ResourceAllocationInfo(self.config_info["cpuAllocation"])

    def _transform_memoryAllocation(self):
        if not self.config_info["memoryAllocation"]:
            return None

        return self._transform_ResourceAllocationInfo(self.config_info["memoryAllocation"])

    def _transform_ResourceAllocationInfo(self, property_name):
        if not self.config_info[property_name]:
            return None

        config_info_allocation = self.config_info[property_name]
        resource_allocation_info = vim.ResourceAllocationInfo()
        resource_allocation_info.expandableReservation = config_info_allocation["expandableReservation"]
        resource_allocation_info.limit = config_info_allocation["limit"]
        resource_allocation_info.reservation = config_info_allocation["reservation"]
        resource_allocation_info.shares = vim.SharesInfo()
        resource_allocation_info.shares.level = config_info_allocation["shares"]["level"]
        resource_allocation_info.shares.shares = config_info_allocation["shares"]["shares"]

        return resource_allocation_info

    def _transform_cpuFeatureMask(self):
        if not self.config_info["cpuFeatureMask"]:
            return []
        cpu_feature_mask = []
        for cpu_id_info in self.config_info["cpuFeatureMask"]:
            cpu_id_info_spec = vim.vm.ConfigSpec.CpuIdInfoSpec()
            cpu_id_info_spec.info = vim.host.CpuIdInfo()
            cpu_id_info_spec.info.eax = cpu_id_info["eax"]
            cpu_id_info_spec.info.ebx = cpu_id_info["ebx"]
            cpu_id_info_spec.info.ecx = cpu_id_info["ecx"]
            cpu_id_info_spec.info.edx = cpu_id_info["edx"]
            cpu_id_info_spec.operation = vim.option.ArrayUpdateSpec.Operation().add
            cpu_feature_mask.append(cpu_id_info_spec)

        return cpu_feature_mask

    def _transform_devices(self):
        device_change = []
        default_devices = [
                "vim.vm.device.VirtualIDEController",
                "vim.vm.device.VirtualPS2Controller",
                "vim.vm.device.VirtualPCIController",
                "vim.vm.device.VirtualSIOController",
                "vim.vm.device.VirtualKeyboard",
                "vim.vm.device.VirtualVMCIDevice",
                "vim.vm.device.VirtualPointingDevice"
                ]

        omitted_devices = [
                "vim.vm.device.VirtualVideoCard",
                ]

        virtual_scsi_controllers = [
                "vim.vm.device.ParaVirtualSCSIController",
                "vim.vm.device.VirtualBusLogicController",
                "vim.vm.device.VirtualLsiLogicController",
                "vim.vm.device.VirtualLsiLogicSASController",
                ]

        virtual_misc_controllers = [
                "vim.vm.device.VirtualNVDIMMController",
                "vim.vm.device.VirtualNVMEController",
                "vim.vm.device.VirtualAHCIController",
                ]

        virtual_usb_controllers = [
                "vim.vm.device.VirtualUSBController",
                "vim.vm.device.VirtualUSBXHCIController",
                ]

        virtual_ethernet_cards = [
                "vim.vm.device.VirtualE1000",
                "vim.vm.device.VirtualE1000e",
                "vim.vm.device.VirtualPCNet32",
                "vim.vm.device.VirtualSriovEthernetCard",
                "vim.vm.device.VirtualVmxnet2",
                "vim.vm.device.VirtualVmxnet3",
                ]

        for device in self.config_info["hardware"]["device"]:
            if device["_vimtype"] in default_devices + omitted_devices:
                continue
            device_spec = vim.vm.device.VirtualDeviceSpec()
            device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation().add
            add_device = None

            if device["_vimtype"] in virtual_scsi_controllers:
                add_device = self._transform_virtual_scsi_controller(device)
            elif device["_vimtype"] in virtual_misc_controllers:
                add_device = self._transform_virtual_misc_controller(device)
            elif device["_vimtype"] in virtual_usb_controllers:
                add_device = self._transform_virtual_usb_controller(device)
            elif device["_vimtype"] == "vim.vm.device.VirtualCdrom":
                add_device = self._transform_virtual_cdrom(device)
            elif device["_vimtype"] == "vim.vm.device.VirtualDisk":
                # print("DEBUG: skipping virtual disks")
                device_spec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation().create
                add_device = self._transform_virtual_disk(device)
            elif device["_vimtype"] in virtual_ethernet_cards:
                add_device = self._transform_virtual_ethernet_card(device)
            else:
                # TODO: raise error, unknown device
                return None

            if add_device:
                device_spec.device = add_device
                device_change.append(device_spec)

        return device_change

    def _transform_virtual_scsi_controller(self, device):
        add_device = None
        if device["_vimtype"] == "vim.vm.device.ParaVirtualSCSIController":
            add_device = vim.vm.device.ParaVirtualSCSIController()
        elif device["_vimtype"] == "vim.vm.device.VirtualBusLogicController":
            add_device = vim.vm.device.VirtualBusLogicController()
        elif device["_vimtype"] == "vim.vm.device.VirtualLsiLogicController":
            add_device = vim.vm.device.VirtualLsiLogicController()
        elif device["_vimtype"] == "vim.vm.device.VirtualLsiLogicSASController":
            add_device = vim.vm.device.VirtualLsiLogicSASController()
        else:
            # TODO: raise error
            return None

        add_device.key = device["key"] * -1
        add_device.busNumber = device["busNumber"]
        add_device.sharedBus = device["sharedBus"]

        return add_device

    def _transform_virtual_misc_controller(self, device):
        add_device = None
        if device["_vimtype"] == "vim.vm.device.VirtualNVDIMMController":
            add_device = vim.vm.device.VirtualNVDIMMController()
        elif device["_vimtype"] == "vim.vm.device.VirtualNVMEController":
            add_device = vim.vm.device.VirtualNVMEController()
        elif device["_vimtype"] == "vim.vm.device.VirtualAHCIController":
            add_device = vim.vm.device.VirtualAHCIController()
        else:
            # TODO: raise error
            return None

        add_device.key = device["key"] * -1
        add_device.busNumber = device["busNumber"]

        return add_device

    def _transform_connectable(self, device):
        connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        connectable.allowGuestControl = device["connectable"]["allowGuestControl"]
        connectable.startConnected = device["connectable"]["startConnected"]
        # connected = True would only make sense for running VM
        connectable.connected = False
        return connectable

    def _transform_virtual_usb_controller(self, device):
        add_device = None
        if device["_vimtype"] == "vim.vm.device.VirtualUSBController":
            add_device = vim.vm.device.VirtualUSBController()
            add_device.ehciEnabled = device["ehciEnabled"]
        elif device["_vimtype"] == "vim.vm.device.VirtualUSBXHCIController":
            add_device = vim.vm.device.VirtualUSBXHCIController()
        else:
            # TODO: unknown type, raise error
            return None

        add_device.key = device["key"] * -1
        add_device.autoConnectDevices = device["autoConnectDevices"]

        return add_device

    def _transform_virtual_cdrom(self, device):
        add_device = vim.vm.device.VirtualCdrom()
        add_device.key = device["key"] * -1
        if device["backing"]["_vimtype"] == "vim.vm.device.VirtualCdrom.AtapiBackingInfo":
            add_device.backing = vim.vm.device.VirtualCdrom.AtapiBackingInfo()
            add_device.backing.deviceName = device["backing"]["deviceName"]
            add_device.backing.useAutoDetect = device["backing"]["useAutoDetect"]
        elif device["backing"]["_vimtype"] == "vim.vm.device.VirtualCdrom.IsoBackingInfo":
            add_device.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo()
            add_device.backing.backingObjectId = device["backing"]["backingObjectId"]
            add_device.backing.datastore = device["backing"]["datastore"]
            add_device.backing.fileName = device["backing"]["fileName"]
        elif device["backing"]["_vimtype"] == "vim.vm.device.VirtualCdrom.PassthroughBackingInfo":
            add_device.backing = vim.vm.device.VirtualCdrom.PassthroughBackingInfo()
            add_device.backing.deviceName = device["backing"]["deviceName"]
            add_device.backing.useAutoDetect = device["backing"]["useAutoDetect"]
        elif device["backing"]["_vimtype"] == "vim.vm.device.VirtualCdrom.RemoteAtapiBackingInfo":
            add_device.backing = vim.vm.device.VirtualCdrom.RemoteAtapiBackingInfo()
            add_device.backing.deviceName = device["backing"]["deviceName"]
            add_device.backing.useAutoDetect = device["backing"]["useAutoDetect"]
        elif device["backing"]["_vimtype"] == "vim.vm.device.VirtualCdrom.RemotePassthroughBackingInfo":
            add_device.backing = vim.vm.device.VirtualCdrom.RemotePassthroughBackingInfo()
            add_device.backing.exclusive = device["backing"]["exclusive"]
            add_device.backing.deviceName = device["backing"]["deviceName"]
            add_device.backing.useAutoDetect = device["backing"]["useAutoDetect"]
        else:
            # TODO: unknown backing type, raise error
            return None

        add_device.connectable = self._transform_connectable(device)

        # TODO: Looks like negative values must not be used for default devices,
        # the second VirtualIDEController seems to have key 201, but is that always the case?
        add_device.controllerKey = device["controllerKey"]
        if device["controllerKey"] != 201:
            add_device.controllerKey = device["controllerKey"] * -1
        add_device.unitNumber = device["unitNumber"]

        return add_device

    def _transform_virtual_disk(self, device):
        add_device = vim.vm.device.VirtualDisk()
        add_device.key = device["key"] * -1
        if device["backing"]["_vimtype"] == "vim.vm.device.VirtualDisk.FlatVer2BackingInfo":
            add_device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
            # this is the datastore MoRef, eg. "vim.Datastore:datastore-13"
            # must be converted to the correct type, otherwise getting
            # TypeError: For "datastore" expected type vim.Datastore, but got str
            # Solution: It works when not specifying the datastore here.
            #add_device.backing.datastore = vim.Datastore(device["backing"]["datastore"])
            add_device.backing.fileName = device["backing"]["fileName"]
            add_device.backing.digestEnabled = device["backing"]["digestEnabled"]
            add_device.backing.diskMode = device["backing"]["diskMode"]
            add_device.backing.eagerlyScrub = device["backing"]["eagerlyScrub"]
            #add_device.backing.keyId = device["backing"]["keyId"]
            add_device.backing.sharing = device["backing"]["sharing"]
            add_device.backing.thinProvisioned = device["backing"]["thinProvisioned"]
            #add_device.backing.uuid = device["backing"]["uuid"]
            add_device.backing.writeThrough = device["backing"]["writeThrough"]
        else:
            # TODO: unsupported backing type, raise error
            return None

        add_device.storageIOAllocation = vim.StorageResourceManager.IOAllocationInfo()
        add_device.storageIOAllocation.shares = vim.SharesInfo()
        add_device.storageIOAllocation.shares.level = device["storageIOAllocation"]["shares"]["level"]
        add_device.storageIOAllocation.shares.shares = device["storageIOAllocation"]["shares"]["shares"]
        add_device.storageIOAllocation.limit = device["storageIOAllocation"]["limit"]
        add_device.storageIOAllocation.reservation = device["storageIOAllocation"]["reservation"]

        add_device.controllerKey = device["controllerKey"] * -1
        add_device.unitNumber = device["unitNumber"]
        add_device.capacityInBytes = device["capacityInBytes"]

        return add_device

    def _transform_virtual_ethernet_card(self, device):
        add_device = None
        if device["_vimtype"] == "vim.vm.device.VirtualE1000":
            add_device = vim.vm.device.VirtualE1000()
        elif device["_vimtype"] == "vim.vm.device.VirtualE1000e":
            add_device = vim.vm.device.VirtualE1000e()
        elif device["_vimtype"] == "vim.vm.device.VirtualPCNet32":
            add_device = vim.vm.device.VirtualPCNet32()
        elif device["_vimtype"] == "vim.vm.device.VirtualSriovEthernetCard":
            add_device = vim.vm.device.VirtualSriovEthernetCard()
        elif device["_vimtype"] == "vim.vm.device.VirtualVmxnet":
            add_device = vim.vm.device.VirtualVmxnet()
        elif device["_vimtype"] == "vim.vm.device.VirtualVmxnet2":
            add_device = vim.vm.device.VirtualVmxnet2()
        elif device["_vimtype"] == "vim.vm.device.VirtualVmxnet3":
            add_device = vim.vm.device.VirtualVmxnet3()
        elif device["_vimtype"] == "vim.vm.device.VirtualVmxnet3Vrdma":
            add_device = vim.vm.device.VirtualVmxnet3Vrdma()
        else:
            # TODO: unknown ethernet card type, raise error
            return None

        if device["backing"]["_vimtype"] == "vim.vm.device.VirtualEthernetCard.NetworkBackingInfo":
            add_device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
            add_device.backing.deviceName = device["backing"]["deviceName"]
            add_device.backing.useAutoDetect = device["backing"]["useAutoDetect"]
            add_device.backing.network = vim.Network(device["backing"]["network"])
        elif device["backing"]["_vimtype"] == "vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo":
            add_device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
            add_device.backing.port = vim.dvs.PortConnection()
            add_device.backing.port.portgroupKey = device["backing"]["port"]["portgroupKey"]
            add_device.backing.port.switchUuid = device["backing"]["port"]["switchUuid"]
        elif device["backing"]["_vimtype"] == "vim.vm.device.VirtualEthernetCard.OpaqueNetworkBackingInfo":
            add_device.backing = vim.vm.device.VirtualEthernetCard.OpaqueNetworkBackingInfo()
            add_device.backing.opaqueNetworkId = device["backing"]["opaqueNetworkId"]
            add_device.backing.opaqueNetworkType = device["backing"]["opaqueNetworkType"]
        elif device["backing"]["_vimtype"] == "vim.vm.device.VirtualEthernetCard.LegacyNetworkBackingInfo":
            add_device.backing = vim.vm.device.VirtualEthernetCard.LegacyNetworkBackingInfo()
            add_device.backing.deviceName = device["backing"]["deviceName"]
            add_device.backing.useAutoDetect = device["backing"]["useAutoDetect"]
        else:
            # TODO: unknown backing type, raise error
            return None

        add_device.key = device["key"] * -1
        add_device.connectable = self._transform_connectable(device)
        # TODO: Looks like negative values must not be used for default devices,
        # the VirtualPCIController seems to have key 100, but is that always the case?
        add_device.controllerKey = device["controllerKey"]
        if device["controllerKey"] != 100:
            add_device.controllerKey = device["controllerKey"] * -1
        add_device.unitNumber = device["unitNumber"]
        # Note: MAC address preservation is only safe with "manual", with "generated" or "assigned" the
        # server may override the specified MAC address
        add_device.addressType = "manual"
        add_device.macAddress = device["macAddress"]
        add_device.externalId = device["externalId"]
        add_device.resourceAllocation = vim.vm.device.VirtualEthernetCard.ResourceAllocation()
        add_device.resourceAllocation.limit = device["resourceAllocation"]["limit"]
        add_device.resourceAllocation.reservation = device["resourceAllocation"]["reservation"]
        add_device.resourceAllocation.share = vim.SharesInfo()
        add_device.resourceAllocation.share.shares = device["resourceAllocation"]["share"]["shares"]
        add_device.resourceAllocation.share.level = device["resourceAllocation"]["share"]["level"]
        add_device.uptCompatibilityEnabled = device["uptCompatibilityEnabled"]
        add_device.wakeOnLanEnabled = device["wakeOnLanEnabled"]

        return add_device

    def _transform_extraConfig(self):
        extra_config = []
        for option_value in self.config_info["extraConfig"]:
            extra_config.append(vim.option.OptionValue())
            extra_config[-1].key = option_value["key"]
            extra_config[-1].value = option_value["value"]

        return extra_config

    def _transform_files(self):
        files = vim.vm.FileInfo()
        files.ftMetadataDirectory = self.config_info["files"]["ftMetadataDirectory"]
        files.logDirectory = self.config_info["files"]["logDirectory"]
        files.snapshotDirectory = self.config_info["files"]["snapshotDirectory"]
        files.suspendDirectory = self.config_info["files"]["suspendDirectory"]
        files.vmPathName = self.config_info["files"]["vmPathName"]

        return files

    def _transform_flags(self):
        flags = vim.vm.FlagInfo()
        flags.cbrcCacheEnabled = self.config_info["flags"]["cbrcCacheEnabled"]
        flags.disableAcceleration = self.config_info["flags"]["disableAcceleration"]
        flags.diskUuidEnabled = self.config_info["flags"]["diskUuidEnabled"]
        flags.enableLogging = self.config_info["flags"]["enableLogging"]
        flags.faultToleranceType = self.config_info["flags"]["faultToleranceType"]
        flags.monitorType = self.config_info["flags"]["monitorType"]
        flags.snapshotLocked = self.config_info["flags"]["snapshotLocked"]
        flags.snapshotPowerOffBehavior = self.config_info["flags"]["snapshotPowerOffBehavior"]
        flags.useToe = self.config_info["flags"]["useToe"]
        flags.vbsEnabled = self.config_info["flags"]["vbsEnabled"]
        flags.virtualExecUsage = self.config_info["flags"]["virtualExecUsage"]
        flags.virtualMmuUsage = self.config_info["flags"]["virtualMmuUsage"]
        flags.vvtdEnabled = self.config_info["flags"]["vvtdEnabled"]

        return flags

    def _transform_ftInfo(self):
        if self.config_info["ftInfo"] is None:
            return None

        ft_info = vim.vm.FaultToleranceConfigInfo()
        ft_info.configPaths = []
        for config_path in self.config_info["ftInfo"]["configPaths"]:
            ft_info.configPaths.append(config_path)
        ft_info.instanceUuids = []
        for instance_uuid in self.config_info["ftInfo"]["instanceUuids"]:
            ft_info.instanceUuids.append(instance_uuid)
        ft_info.role = self.config_info["ftInfo"]["role"]

        return ft_info

    def _transform_guestMonitoringModeInfo(self):
        guest_monitoring_mode_info = vim.vm.GuestMonitoringModeInfo()
        guest_monitoring_mode_info.gmmAppliance = self.config_info["guestMonitoringModeInfo"]["gmmAppliance"]
        guest_monitoring_mode_info.gmmFile = self.config_info["guestMonitoringModeInfo"]["gmmFile"]

        return guest_monitoring_mode_info

    def _transform_latencySensitivity(self, latency_sensitivity_config):
        latency_sensitivity = vim.LatencySensitivity()
        if latency_sensitivity_config["level"] == "custom":
            # Note: custom level is deprecrated since 5.5
            # TODO: raise error
            return None
        latency_sensitivity.level = latency_sensitivity_config["level"]

        return latency_sensitivity

    def _transform_managedBy(self):
        if self.config_info["managedBy"] is None:
            return None

        managed_by = vim.ext.ManagedByInfo()
        managed_by.extensionKey = self.config_info["managedBy"]["extensionKey"]
        managed_by.type = self.config_info["managedBy"]["type"]

        return managed_by

    def _transform_pmem(self):
        if self.config_info["pmem"] is None:
            return None

        pmem = vim.vm.VirtualPMem()
        pmem.snapshotMode = self.config_info["pmem"]["snapshotMode"]

        return pmem

    def _transform_defaultPowerOps(self):
        power_ops = vim.vm.DefaultPowerOpInfo()
        power_ops.defaultPowerOffType = self.config_info["defaultPowerOps"]["defaultPowerOffType"]
        power_ops.defaultResetType = self.config_info["defaultPowerOps"]["defaultResetType"]
        power_ops.defaultSuspendType = self.config_info["defaultPowerOps"]["defaultSuspendType"]
        power_ops.powerOffType = self.config_info["defaultPowerOps"]["powerOffType"]
        power_ops.resetType = self.config_info["defaultPowerOps"]["resetType"]
        power_ops.standbyAction = self.config_info["defaultPowerOps"]["standbyAction"]
        power_ops.suspendType = self.config_info["defaultPowerOps"]["suspendType"]

        return power_ops

    def _transform_sgxInfo(self):
        sgx_info = vim.vm.SgxInfo()
        sgx_info.epcSize = self.config_info["sgxInfo"]["epcSize"]
        sgx_info.flcMode = self.config_info["sgxInfo"]["flcMode"]
        sgx_info.lePubKeyHash = self.config_info["sgxInfo"]["lePubKeyHash"]

        return sgx_info

    def _transform_tools(self):
        tools_config_info = vim.vm.ToolsConfigInfo()
        tools_config_info.afterPowerOn = self.config_info["tools"]["afterPowerOn"]
        tools_config_info.afterResume = self.config_info["tools"]["afterResume"]
        tools_config_info.beforeGuestReboot = self.config_info["tools"]["beforeGuestReboot"]
        tools_config_info.beforeGuestShutdown = self.config_info["tools"]["beforeGuestShutdown"]
        tools_config_info.beforeGuestStandby = self.config_info["tools"]["beforeGuestStandby"]
        tools_config_info.syncTimeWithHost = self.config_info["tools"]["syncTimeWithHost"]
        # Since vSphere API 7.0.1.0
        if "syncTimeWithHostAllowed" in self.config_info["tools"]:
            tools_config_info.syncTimeWithHostAllowed = self.config_info["tools"]["syncTimeWithHostAllowed"]
        tools_config_info.toolsUpgradePolicy = self.config_info["tools"]["toolsUpgradePolicy"]

        return tools_config_info

    def _transform_vAppConfig(self):
        if self.config_info["vAppConfig"] is None:
            return None

        vapp_config_spec = vim.vApp.VmConfigSpec()
        vapp_config_spec.eula = self.config_info["vAppConfig"]["eula"]
        vapp_config_spec.installBootRequired = self.config_info["vAppConfig"]["installBootRequired"]
        vapp_config_spec.installBootStopDelay = self.config_info["vAppConfig"]["installBootStopDelay"]
        vapp_config_spec.ipAssignment = self._transform_VAppIpAssignmentInfo(self.config_info["vAppConfig"]["ipAssignment"])
        vapp_config_spec.ovfEnvironmentTransport = []
        for transport in self.config_info["vAppConfig"]["ovfEnvironmentTransport"]:
            vapp_config_spec.ovfEnvironmentTransport.append(transport)

        vapp_config_spec.ovfSection = self._transform_VAppOvfSectionInfo()
        vapp_config_spec.product = self._transform_VAppProductInfo()
        vapp_config_spec.property = self._transform_VAppPropertyInfo()

        return vapp_config_spec

    def _transform_VAppIpAssignmentInfo(self, ip_assignment_info):

        ip_assignment = vim.vApp.IPAssignmentInfo()
        ip_assignment.ipAllocationPolicy = ip_assignment_info["ipAllocationPolicy"]
        ip_assignment.ipProtocol = ip_assignment_info["ipProtocol"]
        ip_assignment.supportedAllocationScheme = []
        for scheme in ip_assignment_info["supportedAllocationScheme"]:
            ip_assignment.supportedAllocationScheme.append(scheme)
        ip_assignment.supportedIpProtocol = []
        for protocol in ip_assignment_info["supportedIpProtocol"]:
            ip_assignment.supportedIpProtocol.append(protocol)

        return ip_assignment

    def _transform_VAppOvfSectionInfo(self):
        ovf_section_specs = []
        for ovf_section_info in self.config_info["vAppConfig"]["ovfSection"]:
            ovf_section_spec = vim.vApp.OvfSectionSpec()
            ovf_section_spec.operation = "add"
            ovf_section_spec.info = vim.vApp.OvfSectionInfo()
            ovf_section_spec.info.atEnvelopeLevel = ovf_section_info["atEnvelopeLevel"]
            ovf_section_spec.info.contents = ovf_section_info["contents"]
            ovf_section_spec.info.key = ovf_section_info["key"]
            ovf_section_spec.info.namespace = ovf_section_info["namespace"]
            ovf_section_spec.info.type = ovf_section_info["type"]
            ovf_section_specs.append(ovf_section_spec)

        return ovf_section_specs

    def _transform_VAppProductInfo(self):
        product_specs = []
        for product_info in self.config_info["vAppConfig"]["product"]:
            product_spec = vim.vApp.ProductSpec()
            product_spec.operation = "add"
            product_spec.info = vim.vApp.ProductInfo()
            product_spec.info.appUrl = product_info["appUrl"]
            product_spec.info.classId = product_info["classId"]
            product_spec.info.fullVersion = product_info["fullVersion"]
            product_spec.info.instanceId = product_info["instanceId"]
            product_spec.info.key = product_info["key"]
            product_spec.info.name = product_info["name"]
            product_spec.info.productUrl = product_info["productUrl"]
            product_spec.info.vendor = product_info["vendor"]
            product_spec.info.vendorUrl = product_info["vendorUrl"]
            product_spec.info.version = product_info["version"]
            product_specs.append(product_spec)

        return product_specs

    def _transform_VAppPropertyInfo(self):
        property_specs = []
        for property_info in self.config_info["vAppConfig"]["property"]:
            property_spec = vim.vApp.PropertySpec()
            property_spec.operation = "add"
            property_spec.info = vim.vApp.PropertyInfo()
            property_spec.info.category = property_info["category"]
            property_spec.info.classId = property_info["classId"]
            property_spec.info.defaultValue = property_info["defaultValue"]
            property_spec.info.description = property_info["description"]
            property_spec.info.id = property_info["id"]
            property_spec.info.instanceId = property_info["instanceId"]
            property_spec.info.key = property_info["key"]
            property_spec.info.label = property_info["label"]
            property_spec.info.type = property_info["type"]
            property_spec.info.typeReference = property_info["typeReference"]
            property_spec.info.userConfigurable = property_info["userConfigurable"]
            property_spec.info.value = property_info["value"]
            property_specs.append(property_spec)

        return property_specs

    def _transform_VirtualMachineVcpuConfig(self):
        spec_vcpu_configs = []
        for vcpu_config in self.config_info["vcpuConfig"]:
            spec_vcpu_config = vim.vm.VcpuConfig()
            spec_vcpu_config.latencySensitivity = self._transform_latencySensitivity(vcpu_config["latencySensitivity"])
            spec_vcpu_configs.append(spec_vcpu_config)

        return spec_vcpu_configs
