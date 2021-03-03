import numpy as np

from typing import Callable, List, Dict, Tuple, Optional, Union
from mlagents.torch_utils import torch
from mlagents.trainers.torch.encoders import VectorInput
from mlagents.trainers.torch.attention import EntityEmbedding

from mlagents_envs.base_env import ActionSpec, ObservationSpec, DimensionProperty, ObservationType
from mlagents.trainers.settings import NetworkSettings, EncoderType
from mlagents.trainers.torch.networks import SimpleActor

MODEL_FILE = 'models/fast.pt'
EXPORT_FILE = 'models/fast.onnx'
class SerializableSimpleActor(SimpleActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def forward(
        self,
        vec_inputs: List[torch.Tensor],
        vis_inputs: List[torch.Tensor],
        var_len_inputs: List[torch.Tensor],
        masks: Optional[torch.Tensor] = None,
        memories: Optional[torch.Tensor] = None,
    ) -> Tuple[Union[int, torch.Tensor], ...]:
        """
        Note: This forward() method is required for exporting to ONNX. Don't modify the inputs and outputs.
        At this moment, torch.onnx.export() doesn't accept None as tensor to be exported,
        so the size of return tuple varies with action spec.
        """
        # This code will convert the vec and vis obs into a list of inputs for the network
        concatenated_vec_obs = vec_inputs[0]
        inputs = []
        start = 0
        end = 0
        vis_index = 0
        var_len_index = 0
        for i, enc in enumerate(self.network_body.processors):
            if isinstance(enc, VectorInput):
                # This is a vec_obs
                vec_size = self.network_body.embedding_sizes[i]
                end = start + vec_size
                inputs.append(concatenated_vec_obs[:, start:end])
                start = end
            elif isinstance(enc, EntityEmbedding):
                inputs.append(var_len_inputs[var_len_index])
                var_len_index += 1
            else:  # visual input
                inputs.append(vis_inputs[vis_index])
                vis_index += 1

        # End of code to convert the vec and vis obs into a list of inputs for the network
        encoding, memories_out = self.network_body(
            inputs, memories=memories, sequence_length=1
        )

        (
            cont_action_out,
            disc_action_out,
            action_out_deprecated,
        ) = self.action_model.get_action_out(encoding, masks)
        export_out = [self.version_number, self.memory_size_vector]
        if self.action_spec.continuous_size > 0:
            export_out += [cont_action_out, self.continuous_act_size_vector]
        if self.action_spec.discrete_size > 0:
            export_out += [disc_action_out, self.discrete_act_size_vector]
        # Only export deprecated nodes with non-hybrid action spec
        if self.action_spec.continuous_size == 0 or self.action_spec.discrete_size == 0:
            export_out += [
                action_out_deprecated,
                self.is_continuous_int_deprecated,
                self.act_size_vector_deprecated,
            ]
        if self.network_body.memory_size > 0:
            export_out += [memories_out]
        return tuple(export_out)

def export_model(network):
    vec_obs_size = 16
    num_vis_obs = 0
    dummy_vec_obs = [torch.zeros([1] + [vec_obs_size])]
    dummy_vis_obs = []
    dummy_var_len_obs = []
    dummy_masks = torch.ones([1] + [0])
    dummy_memories = torch.zeros([1] + [1] + [256])
    dummy_input = (
        dummy_vec_obs,
        dummy_vis_obs,
        dummy_var_len_obs,
        dummy_masks,
        dummy_memories,
    )
    input_names = ['vector_observation', 'action_masks', 'recurrent_in']
    dynamic_axes = {name: {0: "batch"} for name in input_names}
    output_names = ['version_number', 'memory_size', 'continuous_actions', 'continuous_action_output_shape', 'action', 'is_continuous_control', 'action_output_shape', 'recurrent_out']
    dynamic_axes.update({'continuous_actions': {0: "batch"}})
    dynamic_axes.update({'action': {0: "batch"}})

    torch.onnx.export(
        network,
        dummy_input,
        EXPORT_FILE,
        opset_version=9,
        input_names=input_names,
        output_names=output_names,
        dynamic_axes=dynamic_axes
    )

if __name__ == '__main__':
    obs_spec = [ObservationSpec(shape=(16,), dimension_property=(DimensionProperty.UNSPECIFIED,), observation_type=ObservationType.DEFAULT)]
    act_spec = ActionSpec(continuous_size=4, discrete_branches=())
    net_settings = NetworkSettings(normalize=False, hidden_units=256, num_layers=2, vis_encode_type=EncoderType.SIMPLE, memory=NetworkSettings.MemorySettings(sequence_length=64, memory_size=256))

    network = SerializableSimpleActor(obs_spec, net_settings, act_spec)
    state_dict = torch.load(MODEL_FILE, map_location=torch.device('cpu'))
    filtered_sd = {i:j for i, j in state_dict['Policy'].items() if 'critic' not in i}
    network.load_state_dict(filtered_sd)

    export_model(network)
