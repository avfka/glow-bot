/**
 * Типы схемы Supabase.
 *
 * Сгенерированы по миграциям из supabase/migrations.
 * После изменения схемы перегенерировать:
 *   supabase gen types typescript --linked > src/types/database.ts
 */

export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[];

export type SkinType = 'normal' | 'dry' | 'oily' | 'combination' | 'sensitive';
export type AppointmentStatus = 'scheduled' | 'done' | 'cancelled' | 'no_show';
export type PhotoKind = 'before' | 'after';
export type AnalysisSource = 'text' | 'photo';

export interface Database {
  public: {
    Tables: {
      specialists: {
        Row: {
          id: string;
          telegram_id: number;
          name: string;
          specialization: string;
          phone: string;
          avatar_url: string | null;
          onboarded_at: string | null;
          created_at: string;
        };
        Insert: {
          id: string;
          telegram_id: number;
          name?: string;
          specialization?: string;
          phone?: string;
          avatar_url?: string | null;
          onboarded_at?: string | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          telegram_id?: number;
          name?: string;
          specialization?: string;
          phone?: string;
          avatar_url?: string | null;
          onboarded_at?: string | null;
          created_at?: string;
        };
        Relationships: [];
      };
      clients: {
        Row: {
          id: string;
          specialist_id: string;
          name: string;
          phone: string;
          telegram_username: string;
          skin_type: SkinType | null;
          allergies: string;
          contraindications: string;
          notes: string;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          specialist_id: string;
          name: string;
          phone?: string;
          telegram_username?: string;
          skin_type?: SkinType | null;
          allergies?: string;
          contraindications?: string;
          notes?: string;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          specialist_id?: string;
          name?: string;
          phone?: string;
          telegram_username?: string;
          skin_type?: SkinType | null;
          allergies?: string;
          contraindications?: string;
          notes?: string;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'clients_specialist_id_fkey';
            columns: ['specialist_id'];
            isOneToOne: false;
            referencedRelation: 'specialists';
            referencedColumns: ['id'];
          },
        ];
      };
      services: {
        Row: {
          id: string;
          specialist_id: string;
          name: string;
          duration_min: number;
          price: number;
          description: string;
          is_active: boolean;
          created_at: string;
        };
        Insert: {
          id?: string;
          specialist_id: string;
          name: string;
          duration_min?: number;
          price?: number;
          description?: string;
          is_active?: boolean;
          created_at?: string;
        };
        Update: {
          id?: string;
          specialist_id?: string;
          name?: string;
          duration_min?: number;
          price?: number;
          description?: string;
          is_active?: boolean;
          created_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'services_specialist_id_fkey';
            columns: ['specialist_id'];
            isOneToOne: false;
            referencedRelation: 'specialists';
            referencedColumns: ['id'];
          },
        ];
      };
      appointments: {
        Row: {
          id: string;
          specialist_id: string;
          client_id: string;
          service_id: string | null;
          starts_at: string;
          duration_min: number;
          price: number;
          status: AppointmentStatus;
          note: string;
          remind_before_min: number | null;
          reminded_at: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          specialist_id: string;
          client_id: string;
          service_id?: string | null;
          starts_at: string;
          duration_min?: number;
          price?: number;
          status?: AppointmentStatus;
          note?: string;
          remind_before_min?: number | null;
          reminded_at?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          specialist_id?: string;
          client_id?: string;
          service_id?: string | null;
          starts_at?: string;
          duration_min?: number;
          price?: number;
          status?: AppointmentStatus;
          note?: string;
          remind_before_min?: number | null;
          reminded_at?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'appointments_specialist_id_fkey';
            columns: ['specialist_id'];
            isOneToOne: false;
            referencedRelation: 'specialists';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'appointments_client_id_fkey';
            columns: ['client_id'];
            isOneToOne: false;
            referencedRelation: 'clients';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'appointments_service_id_fkey';
            columns: ['service_id'];
            isOneToOne: false;
            referencedRelation: 'services';
            referencedColumns: ['id'];
          },
        ];
      };
      client_photos: {
        Row: {
          id: string;
          specialist_id: string;
          client_id: string;
          appointment_id: string | null;
          kind: PhotoKind;
          storage_path: string;
          taken_at: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          specialist_id: string;
          client_id: string;
          appointment_id?: string | null;
          kind: PhotoKind;
          storage_path: string;
          taken_at?: string;
          created_at?: string;
        };
        Update: {
          id?: string;
          specialist_id?: string;
          client_id?: string;
          appointment_id?: string | null;
          kind?: PhotoKind;
          storage_path?: string;
          taken_at?: string;
          created_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'client_photos_specialist_id_fkey';
            columns: ['specialist_id'];
            isOneToOne: false;
            referencedRelation: 'specialists';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'client_photos_client_id_fkey';
            columns: ['client_id'];
            isOneToOne: false;
            referencedRelation: 'clients';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'client_photos_appointment_id_fkey';
            columns: ['appointment_id'];
            isOneToOne: false;
            referencedRelation: 'appointments';
            referencedColumns: ['id'];
          },
        ];
      };
      ingredient_analyses: {
        Row: {
          id: string;
          specialist_id: string;
          client_id: string | null;
          source: AnalysisSource;
          input_text: string;
          result: Json;
          model: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          specialist_id: string;
          client_id?: string | null;
          source: AnalysisSource;
          input_text?: string;
          result: Json;
          model: string;
          created_at?: string;
        };
        Update: {
          id?: string;
          specialist_id?: string;
          client_id?: string | null;
          source?: AnalysisSource;
          input_text?: string;
          result?: Json;
          model?: string;
          created_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'ingredient_analyses_specialist_id_fkey';
            columns: ['specialist_id'];
            isOneToOne: false;
            referencedRelation: 'specialists';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'ingredient_analyses_client_id_fkey';
            columns: ['client_id'];
            isOneToOne: false;
            referencedRelation: 'clients';
            referencedColumns: ['id'];
          },
        ];
      };
    };
    Views: Record<string, never>;
    Functions: Record<string, never>;
    Enums: {
      skin_type: SkinType;
      appointment_status: AppointmentStatus;
      photo_kind: PhotoKind;
      analysis_source: AnalysisSource;
    };
    CompositeTypes: Record<string, never>;
  };
}
