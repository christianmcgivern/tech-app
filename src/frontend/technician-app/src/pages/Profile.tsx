import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Avatar,
  Grid,
  Divider,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
} from '@mui/material';
import { useTechnicianStore } from '../store/technicianStore';
import { api } from '../services/api';

interface TechnicianProfile {
  id: number;
  name: string;
  phone: string;
  active: boolean;
}

interface Activity {
  id: number;
  type: string;
  description: string;
  time: string;
}

const Profile: React.FC = () => {
  const { technicianId, truckId } = useTechnicianStore();
  const [profile, setProfile] = useState<TechnicianProfile | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        if (technicianId) {
          const [profileData, activityData] = await Promise.all([
            api.getTechnicianProfile(technicianId),
            api.getTechnicianActivity(technicianId),
          ]);
          setProfile(profileData);
          setActivities(activityData);
        }
      } catch (error) {
        console.error('Error fetching profile data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [technicianId]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (!profile) {
    return (
      <Box>
        <Typography variant="h6" color="error">
          Error loading profile
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Profile
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar
                sx={{
                  width: 100,
                  height: 100,
                  margin: '0 auto 16px',
                  bgcolor: 'primary.main',
                }}
              >
                {profile.name.split(' ').map(n => n[0]).join('')}
              </Avatar>
              <Typography variant="h5" gutterBottom>
                {profile.name}
              </Typography>
              <Typography color="text.secondary" gutterBottom>
                {profile.phone}
              </Typography>
              <Typography variant="body2">
                Truck {truckId} • {profile.active ? 'Active' : 'Inactive'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              <List>
                {activities.map((activity, index) => (
                  <React.Fragment key={activity.id}>
                    {index > 0 && <Divider />}
                    <ListItem>
                      <ListItemText
                        primary={activity.type}
                        secondary={
                          <>
                            <Typography component="span" variant="body2" color="text.primary">
                              {activity.description}
                            </Typography>
                            {' — '}
                            {activity.time}
                          </>
                        }
                      />
                    </ListItem>
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Profile; 