import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  IconButton,
  AppBar,
  Toolbar,
  TextField,
  Button,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import { useTechnicianStore } from '../store/technicianStore';
import { api } from '../services/api';

interface InventoryItem {
  id: number;
  name: string;
  category: string;
  quantity: number;
  unit?: string;
}

const Inventory: React.FC = () => {
  const navigate = useNavigate();
  const { technicianId, truckId } = useTechnicianStore();
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingItem, setEditingItem] = useState<number | null>(null);
  const [editQuantity, setEditQuantity] = useState<number>(0);

  useEffect(() => {
    const fetchInventory = async () => {
      try {
        const data = await api.getTruckInventory(truckId!);
        setInventory(data);
      } catch (error) {
        console.error('Error fetching inventory:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchInventory();
  }, [truckId]);

  const handleUpdateQuantity = async (itemId: number) => {
    if (!truckId) return;
    try {
      await api.updateTruckInventory(truckId, itemId, editQuantity);
      const data = await api.getTruckInventory(truckId);
      setInventory(data);
      setEditingItem(null);
    } catch (error) {
      console.error('Error updating quantity:', error);
    }
  };

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => navigate('/dashboard')}
            sx={{ mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h6">
            Truck Inventory
          </Typography>
        </Toolbar>
      </AppBar>

      <Box sx={{ p: 2 }}>
        {loading ? (
          <Typography>Loading inventory...</Typography>
        ) : inventory.length === 0 ? (
          <Typography>No inventory items found</Typography>
        ) : (
          <List>
            {inventory.map((item) => (
              <ListItem
                key={item.id}
                divider
                sx={{ flexDirection: 'column', alignItems: 'flex-start' }}
              >
                <Box sx={{ width: '100%', display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                    {item.name}
                  </Typography>
                  {item.quantity < 5 && (
                    <Chip
                      label="Low Stock"
                      color="error"
                      size="small"
                    />
                  )}
                </Box>
                <ListItemText
                  secondary={
                    <>
                      <Typography variant="body2" color="text.secondary">
                        Category: {item.category}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Quantity: {item.quantity} {item.unit || 'units'}
                      </Typography>
                    </>
                  }
                />
                {editingItem === item.id ? (
                  <Box sx={{ mt: 1, display: 'flex', gap: 1, width: '100%' }}>
                    <TextField
                      type="number"
                      size="small"
                      value={editQuantity}
                      onChange={(e) => setEditQuantity(Number(e.target.value))}
                      sx={{ width: '100px' }}
                    />
                    <Button
                      variant="contained"
                      size="small"
                      onClick={() => handleUpdateQuantity(item.id)}
                    >
                      Update
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => setEditingItem(null)}
                    >
                      Cancel
                    </Button>
                  </Box>
                ) : (
                  <Button
                    variant="outlined"
                    size="small"
                    sx={{ mt: 1 }}
                    onClick={() => {
                      setEditingItem(item.id);
                      setEditQuantity(item.quantity);
                    }}
                  >
                    Update Quantity
                  </Button>
                )}
              </ListItem>
            ))}
          </List>
        )}
      </Box>
    </Box>
  );
};

export default Inventory; 