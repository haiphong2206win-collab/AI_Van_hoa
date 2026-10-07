"""Reference copied from vqa_scratch.ipynb cell 29, for tests only.
Changes: no pretrained downloads; T5 constructed from provided synthetic config.
No checkpoint from the user is included.
"""
import math
import torch
import torch.nn as nn
import torchvision
from transformers import AutoModelForSeq2SeqLM
class CFG:
    NUM_VISUAL_TOKENS = 16
    FREEZE_IMAGE_BACKBONE_LAYERS = 7
    GEN_MAX_LENGTH = 8
    GEN_NUM_BEAMS = 2
    TEST_CONFIG = None

class ImageEncoder(nn.Module):
    '''Trích đặc trưng ảnh dạng LƯỚI (grid features) thay vì 1 vector toàn cục — giữ lại thông
    tin không gian, sau đó chiếu mỗi ô lưới thành 1 "visual token" cùng chiều với embedding
    của ViT5 để nối trực tiếp vào chuỗi input của encoder (giống cách ghép ảnh+chữ trong các
    mô hình vision-language dạng "visual prefix").'''
    def __init__(self, d_model, num_visual_tokens=CFG.NUM_VISUAL_TOKENS,
                 freeze_layers=CFG.FREEZE_IMAGE_BACKBONE_LAYERS):
        super().__init__()
        # ResNet101: cùng feat_dim=2048 như ResNet50 (khác biệt duy nhất là layer3 có 23 block
        # thay vì 6 block) nên phần projector/pooling phía dưới không cần thay đổi gì.
        backbone = torchvision.models.resnet101(weights=None)
        self.feat_dim = backbone.fc.in_features  # 2048
        # Bỏ avgpool + fc để giữ lại feature map không gian (B, 2048, H, W)
        self.backbone = nn.Sequential(*list(backbone.children())[:-2])

        children = list(self.backbone.children())
        freeze_upto = min(freeze_layers, len(children))
        for layer in children[:freeze_upto]:
            for p in layer.parameters():
                p.requires_grad = False

        grid_side = int(math.sqrt(num_visual_tokens))
        assert grid_side * grid_side == num_visual_tokens, "NUM_VISUAL_TOKENS phải là số chính phương (4, 9, 16, 25...)"
        self.pool = nn.AdaptiveAvgPool2d((grid_side, grid_side))
        self.num_visual_tokens = num_visual_tokens

        self.projector = nn.Sequential(
            nn.Linear(self.feat_dim, d_model),
            nn.GELU(),
            nn.LayerNorm(d_model),
            nn.Dropout(0.1),
        )

    def forward(self, images):
        feat_map = self.backbone(images)            # (B, 2048, H, W)
        pooled = self.pool(feat_map)                 # (B, 2048, grid, grid)
        B, C, gh, gw = pooled.shape
        tokens = pooled.flatten(2).transpose(1, 2)    # (B, grid*grid, 2048)
        tokens = self.projector(tokens)               # (B, num_visual_tokens, d_model)
        return tokens

class VQAGenModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.seq2seq = AutoModelForSeq2SeqLM.from_config(CFG.TEST_CONFIG)
        self.d_model = self.seq2seq.config.d_model
        self.image_encoder = ImageEncoder(self.d_model, CFG.NUM_VISUAL_TOKENS)

    def _combine_encoder_inputs(self, images, input_ids, attention_mask):
        img_tokens = self.image_encoder(images)                                  # (B, K, d_model)
        text_embeds = self.seq2seq.get_input_embeddings()(input_ids)              # (B, L, d_model)
        combined_embeds = torch.cat([img_tokens, text_embeds], dim=1)             # (B, K+L, d_model)
        img_mask = torch.ones(images.size(0), img_tokens.size(1),
                               dtype=attention_mask.dtype, device=attention_mask.device)
        combined_mask = torch.cat([img_mask, attention_mask], dim=1)
        return combined_embeds, combined_mask

    def forward(self, images, input_ids, attention_mask, labels=None):
        combined_embeds, combined_mask = self._combine_encoder_inputs(images, input_ids, attention_mask)
        return self.seq2seq(inputs_embeds=combined_embeds, attention_mask=combined_mask, labels=labels)

    @torch.no_grad()
    def generate(self, images, input_ids, attention_mask,
                 max_length=CFG.GEN_MAX_LENGTH, num_beams=CFG.GEN_NUM_BEAMS):
        combined_embeds, combined_mask = self._combine_encoder_inputs(images, input_ids, attention_mask)
        encoder = self.seq2seq.get_encoder()
        encoder_outputs = encoder(inputs_embeds=combined_embeds, attention_mask=combined_mask)
        return self.seq2seq.generate(
            encoder_outputs=encoder_outputs,
            attention_mask=combined_mask,
            max_length=max_length,
            num_beams=num_beams,
            early_stopping=True,
        )
