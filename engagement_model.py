"""
Engagement Classification Model Architecture
Matches the trained model structure for inference
"""

import torch
import torch.nn as nn


class EngagementCNN(nn.Module):
    """
    CNN model for student engagement classification
    Architecture matches the trained best_model_state.bin
    
    Classes:
    0: Engaged_engaged
    1: Engaged_confused
    2: Engaged_frustrated
    3: Not engaged_Looking Away
    4: Not engaged_bored
    5: Not engaged_drowsy
    """
    
    def __init__(self, num_classes=6):
        super(EngagementCNN, self).__init__()
        
        # First convolutional block (matches actual trained model)
        self.conv2Dblock1 = nn.Sequential(
            # Conv layer 1: 1 -> 16
            nn.Conv2d(in_channels=1, out_channels=16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(p=0.3),
            
            # Conv layer 2: 16 -> 32
            nn.Conv2d(in_channels=16, out_channels=32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(p=0.3),
            
            # Conv layer 3: 32 -> 64
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(p=0.3),
        )
        
        # Second convolutional block (matches actual trained model)
        self.conv2Dblock2 = nn.Sequential(
            # Conv layer 4: 1 -> 32 (note: input is 1 channel, not 64)
            nn.Conv2d(in_channels=1, out_channels=32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(p=0.3),
            
            # Conv layer 5: 32 -> 64
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=5, padding=2),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(p=0.3),
            
            # Conv layer 6: 64 -> 128
            nn.Conv2d(in_channels=64, out_channels=128, kernel_size=7, padding=3),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(p=0.3),
        )
        
        # Fully connected layer
        # Input size: 9408 (from actual model)
        self.fc1_linear = nn.Linear(9408, num_classes)
    
    def forward(self, x):
        """
        Forward pass
        
        Args:
            x: Input tensor (batch_size, 1, 224, 224) - grayscale
            
        Returns:
            Output logits (batch_size, num_classes)
        """
        # Process through both blocks independently
        x1 = self.conv2Dblock1(x)  # First path: (batch, 64, 28, 28)
        x2 = self.conv2Dblock2(x)  # Second path: (batch, 128, 28, 28)
        
        # Adaptive pooling to 7x7
        pool = nn.AdaptiveAvgPool2d((7, 7))
        x1 = pool(x1)  # (batch, 64, 7, 7)
        x2 = pool(x2)  # (batch, 128, 7, 7)
        
        # Flatten both
        x1_flat = x1.view(x1.size(0), -1)  # (batch, 3136)
        x2_flat = x2.view(x2.size(0), -1)  # (batch, 6272)
        
        # Concatenate
        x_combined = torch.cat([x1_flat, x2_flat], dim=1)  # (batch, 9408)
        
        # Fully connected
        x = self.fc1_linear(x_combined)
        
        return x


def load_engagement_model(model_path='best_model_state.bin', device='cpu'):
    """
    Load the trained engagement model
    
    Args:
        model_path: Path to model weights
        device: Device to load model on ('cpu' or 'cuda')
        
    Returns:
        Loaded model in eval mode
    """
    # Create model
    model = EngagementCNN(num_classes=6)
    
    # Load weights
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)
    
    # Set to evaluation mode
    model.eval()
    model.to(device)
    
    return model


# Class names and their indices
CLASS_NAMES = {
    0: 'Engaged_engaged',
    1: 'Engaged_confused',
    2: 'Engaged_frustrated',
    3: 'Not engaged_Looking Away',
    4: 'Not engaged_bored',
    5: 'Not engaged_drowsy'
}

# Simplified class names for display
CLASS_DISPLAY_NAMES = {
    0: 'Engaged',
    1: 'Confused',
    2: 'Frustrated',
    3: 'Looking Away',
    4: 'Bored',
    5: 'Drowsy'
}

# Scoring weights for each class
CLASS_WEIGHTS = {
    0: 2,   # Engaged_engaged
    1: 1,   # Engaged_confused
    2: 0,   # Engaged_frustrated
    3: -1,  # Not engaged_Looking Away
    4: -1,  # Not engaged_bored
    5: -2   # Not engaged_drowsy
}
