import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Container,
  SelectChangeEvent,
  CircularProgress,
  Alert,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useTechnicianStore } from '../store/technicianStore';
import { api } from '../services/api';

interface Technician {
  id: number;
  name: string;
  active: boolean;
}

interface Truck {
  id: number;
  name: string;
  status: string;
}

const TechnicianSelect: React.FC = () => {
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [trucks, setTrucks] = useState<Truck[]>([]);
  const [selectedTech, setSelectedTech] = useState('');
  const [selectedTruck, setSelectedTruck] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { setTechnician, setTruck } = useTechnicianStore();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [techData, truckData] = await Promise.all([
          api.getActiveTechnicians(),
          api.getAvailableTrucks()
        ]);
        setTechnicians(techData);
        setTrucks(truckData);
      } catch (err) {
        setError('Failed to load technicians and trucks. Please try again.');
        console.error('Error fetching data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleTechChange = (event: SelectChangeEvent) => {
    setSelectedTech(event.target.value);
  };

  const handleTruckChange = (event: SelectChangeEvent) => {
    setSelectedTruck(event.target.value);
  };

  const handleStartDay = async () => {
    if (selectedTech && selectedTruck) {
      try {
        // Clock in the technician with truck_id
        await api.clockIn(selectedTech, { truck_id: parseInt(selectedTruck) });
        
        // Update the app state
        setTechnician(selectedTech);
        setTruck(selectedTruck);
        
        // Navigate to the dashboard
        navigate('/dashboard');
      } catch (err: any) {
        if (err.response?.status === 422 && err.response?.data?.detail?.includes("already has an active clock-in record")) {
          // If already clocked in, just update state and continue
          setTechnician(selectedTech);
          setTruck(selectedTruck);
          navigate('/dashboard');
        } else {
          setError(err.response?.data?.detail || 'Failed to start day. Please try again.');
          console.error('Error starting day:', err);
        }
      }
    }
  };

  if (loading) {
    return (
      <Container sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="sm" sx={{ height: '100vh', display: 'flex', alignItems: 'center' }}>
      <Card sx={{ width: '100%', maxWidth: 400, mx: 'auto' }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom align="center" sx={{ mb: 4 }}>
            Welcome to Tech App
          </Typography>
          
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          
          <Box sx={{ mb: 3 }}>
            <FormControl fullWidth>
              <InputLabel>Select Technician</InputLabel>
              <Select
                value={selectedTech}
                label="Select Technician"
                onChange={handleTechChange}
                sx={{ mb: 2 }}
              >
                {technicians.map((tech) => (
                  <MenuItem key={tech.id} value={tech.id}>
                    {tech.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          <Box sx={{ mb: 4 }}>
            <FormControl fullWidth>
              <InputLabel>Select Truck</InputLabel>
              <Select
                value={selectedTruck}
                label="Select Truck"
                onChange={handleTruckChange}
              >
                {trucks.map((truck) => (
                  <MenuItem key={truck.id} value={truck.id}>
                    {truck.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          <Button
            variant="contained"
            fullWidth
            size="large"
            onClick={handleStartDay}
            disabled={!selectedTech || !selectedTruck}
            sx={{ mt: 2 }}
          >
            Start Day
          </Button>
        </CardContent>
      </Card>
    </Container>
  );
};

export default TechnicianSelect; 