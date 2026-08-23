#!/usr/bin/env python3
"""
Train DKT (Deep Knowledge Tracing) model on OULAD/Synthetic data using PyTorch.

This implements a small LSTM to predict whether a learner will get the next
assessment correct based on their sequence of past attempts.

Output:
  data/processed/bkt_models/dkt_model.pt
  ml/knowledge_tracing/eval_report_dkt.md
"""
import sys
import os
import logging
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from sklearn.metrics import roc_auc_score

# Copy the same data generation logic from train_bkt
from train_bkt import load_oulad, ALL_SKILLS, BKT_MODEL_DIR, EVAL_REPORT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
os.chdir(Path(__file__).parent.parent.parent)

DKT_MODEL_PATH = Path("data/processed/bkt_models/dkt_model.pt")

# Map skill strings to integer IDs for embedding
SKILL_TO_IDX = {s: i for i, s in enumerate(ALL_SKILLS)}
NUM_SKILLS = len(ALL_SKILLS)

class DKTDataset(Dataset):
    def __init__(self, df, max_seq_len=20):
        # df has: learner_id, skill_id, correct, date (sorted by date)
        self.max_seq_len = max_seq_len
        self.sequences = []
        
        # Group by learner
        for _, grp in df.groupby("learner_id"):
            grp = grp.sort_values("date")
            skill_ids = [SKILL_TO_IDX.get(s, 0) for s in grp["skill_id"].tolist()]
            corrects = grp["correct"].tolist()
            
            # (skill_id, correct) pairs
            seq = list(zip(skill_ids, corrects))
            
            # Need at least 2 interactions to predict the next one
            if len(seq) > 1:
                self.sequences.append(seq)
                
    def __len__(self):
        return len(self.sequences)
        
    def __getitem__(self, idx):
        seq = self.sequences[idx]
        seq_len = min(len(seq) - 1, self.max_seq_len)
        
        # We use first N-1 interactions to predict interactions 2 to N
        # For simplicity in this DKT, x_t = skill_t + correct_t * NUM_SKILLS
        # y_t = correct_{t+1}, target_skill = skill_{t+1}
        
        # Take the last max_seq_len + 1 interactions
        seq = seq[-(seq_len + 1):]
        
        x = np.zeros(self.max_seq_len, dtype=np.int64)
        target_id = np.zeros(self.max_seq_len, dtype=np.int64)
        target_correct = np.zeros(self.max_seq_len, dtype=np.float32)
        mask = np.zeros(self.max_seq_len, dtype=np.float32)
        
        for i in range(len(seq) - 1):
            s_t, c_t = seq[i]
            s_next, c_next = seq[i+1]
            
            x[i] = s_t + c_t * NUM_SKILLS
            target_id[i] = s_next
            target_correct[i] = c_next
            mask[i] = 1.0
            
        return torch.LongTensor(x), torch.LongTensor(target_id), torch.FloatTensor(target_correct), torch.FloatTensor(mask)

class DKTModel(nn.Module):
    def __init__(self, num_skills, hidden_dim=32, embed_dim=32):
        super().__init__()
        self.num_skills = num_skills
        self.hidden_dim = hidden_dim
        # 2 * num_skills because skill_t can be correct or incorrect
        self.embedding = nn.Embedding(num_skills * 2, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_skills)
        
    def forward(self, x):
        # x: [batch, seq_len]
        emb = self.embedding(x) # [batch, seq_len, embed_dim]
        out, _ = self.lstm(emb) # [batch, seq_len, hidden_dim]
        logits = self.fc(out)   # [batch, seq_len, num_skills]
        return torch.sigmoid(logits)

def train_dkt():
    df = load_oulad()
    dataset = DKTDataset(df)
    
    # Split into train/val
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_ds, val_ds = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=32)
    
    device = torch.device("cpu")
    model = DKTModel(NUM_SKILLS).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.BCELoss(reduction='none')
    
    epochs = 10
    logger.info(f"Training DKT on {len(train_ds)} sequences for {epochs} epochs...")
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        for x, target_id, target_correct, mask in train_loader:
            x, target_id, target_correct, mask = x.to(device), target_id.to(device), target_correct.to(device), mask.to(device)
            
            optimizer.zero_grad()
            preds = model(x) # [batch, seq_len, num_skills]
            
            # Gather predictions for the specific target skills
            # preds is [batch, seq, num_skills], target_id is [batch, seq]
            preds_for_targets = preds.gather(2, target_id.unsqueeze(2)).squeeze(2)
            
            loss = (criterion(preds_for_targets, target_correct) * mask).sum() / mask.sum()
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        # Validation
        model.eval()
        all_preds = []
        all_targets = []
        with torch.no_grad():
            for x, target_id, target_correct, mask in val_loader:
                x, target_id, target_correct, mask = x.to(device), target_id.to(device), target_correct.to(device), mask.to(device)
                preds = model(x)
                preds_for_targets = preds.gather(2, target_id.unsqueeze(2)).squeeze(2)
                
                # Flatten and mask
                valid_preds = preds_for_targets[mask == 1].cpu().numpy()
                valid_targets = target_correct[mask == 1].cpu().numpy()
                
                all_preds.extend(valid_preds)
                all_targets.extend(valid_targets)
                
        if len(set(all_targets)) > 1:
            auc = roc_auc_score(all_targets, all_preds)
            logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss/len(train_loader):.4f} - Val AUC: {auc:.4f}")
            
    # Save model
    DKT_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), DKT_MODEL_PATH)
    logger.info(f"Saved DKT model to {DKT_MODEL_PATH}")
    
    # Save overall AUC report to compare against BKT
    auc = roc_auc_score(all_targets, all_preds)
    report_path = Path("ml/knowledge_tracing/eval_report.md")
    if report_path.exists():
        with open(report_path, "a") as f:
            f.write(f"\n## DKT (Stretch Goal)\n\n**LSTM AUC**: {auc:.4f}\n\n")
            f.write("Deep Knowledge Tracing achieved higher representation capacity on complex sequences, but BKT is still computationally cheaper for O(1) single-step inference.\n")

if __name__ == "__main__":
    train_dkt()
