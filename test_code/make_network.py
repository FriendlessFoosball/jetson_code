from mlagents_envs.base_env import ActionSpec, ObservationSpec, DimensionProperty, ObservationType
from mlagents.trainers.settings import NetworkSettings, EncoderType

obs_spec = [ObservationSpec(shape=(16,), dimension_property=(DimensionProperty.UNSPECIFIED,), observation_type=ObservationType.DEFAULT)]
act_spec = ActionSpec(continuous_size=4, discrete_branches=())
net_settings = NetworkSettings(normalize=False, hidden_units=256, num_layers=2, vis_encode_type=EncoderType.SIMPLE, memory=None)

