#!/usr/bin/env python3
import torch

from diffusers import DiffusionPipeline


# TODO(Patrick, Anton, Suraj) - rename `x` to better variable names
class ScoreSdeVePipeline(DiffusionPipeline):
    def __init__(self, model, scheduler):
        super().__init__()
        self.register_modules(model=model, scheduler=scheduler)

    def __call__(self, num_inference_steps=2000, generator=None):
        device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

        img_size = self.model.config.image_size
        shape = (1, 3, img_size, img_size)

        model = self.model.to(device)

        sample = torch.randn(*shape) * self.scheduler.config.sigma_max
        sample = sample.to(device)

        self.scheduler.set_timesteps(num_inference_steps)
        self.scheduler.set_sigmas(num_inference_steps)

        for i, t in enumerate(self.scheduler.timesteps):
            sigma_t = self.scheduler.sigmas[i] * torch.ones(shape[0], device=device)

            for _ in range(self.scheduler.correct_steps):
                with torch.no_grad():
                    model_output = self.model(sample, sigma_t)

                if isinstance(model_output, dict):
                    model_output = model_output["sample"]

                sample = self.scheduler.step_correct(model_output, sample)["prev_sample"]

            with torch.no_grad():
                model_output = model(sample, sigma_t)

                if isinstance(model_output, dict):
                    model_output = model_output["sample"]

            output = self.scheduler.step_pred(model_output, t, sample)
            sample, sample_mean = output["prev_sample"], output["prev_sample_mean"]

        return sample_mean
